#include <tvm/packed_func_ext.h>
#include <tvm/runtime/device_api.h>
#include <tvm/relay/expr_functor.h>
#include <tvm/relay/pattern_functor.h>
#include <tvm/relay/interpreter.h>
#include <tvm/relay/transform.h>
#include <tvm/relay/analysis.h>
#include <tvm/relay/attrs/debug.h>
#include <tvm/relay/feature.h>
#include "compile_engine.h"

namespace tvm {
namespace relay {

class Interpreter :
      public ExprFunctor<Value(const Expr& n)>,
             PatternFunctor<bool(const Pattern& p, const Value& v)> {
 public:
  Array<Shape> ComputeDynamicShape(const Function& func,
                                   const Array<Value>& args) {
    auto key = CCacheKeyNode::make(func, Target::Create("llvm"));
    auto cfunc = engine_->LowerShapeFunc(key);
    size_t arity = cfunc->inputs.size() + cfunc->outputs.size();

    std::vector<TVMValue> values(arity);
    std::vector<int> codes(arity);
    TVMArgsSetter setter(values.data(), codes.data());
    std::vector<NDArray> inputs(cfunc->inputs.size());
    std::vector<NDArray> outputs(cfunc->outputs.size());

    DLContext cpu_ctx;
    cpu_ctx.device_type = kDLCPU;
    cpu_ctx.device_id = 0;

    auto fset_input = [&](size_t i, Value val, bool need_shape) {
        const TensorValueNode* tv = val.as<TensorValueNode>();
        CHECK(tv != nullptr) << "expect Tensor argument";
        if (need_shape) {
          int64_t ndim = tv->data.Shape().size();
          NDArray shape_arr;
          if (ndim == 0) {
            shape_arr = NDArray::Empty({}, DataType::Int(64), cpu_ctx);
          } else {
            shape_arr = NDArray::Empty({ndim}, DataType::Int(64), cpu_ctx);
            int64_t* data = reinterpret_cast<int64_t*>(shape_arr->data);
            for (auto j = 0; j < ndim; ++j) {
              data[j] = tv->data.Shape()[j];
            }
          }
          inputs[i] = shape_arr;
          setter(i, shape_arr);
        } else {
          auto arr = tv->data.CopyTo(cpu_ctx);
          inputs[i] = arr;
          setter(i, arr);
        }
    };

    size_t arg_counter = 0;
    for (size_t i = 0; i < args.size(); ++i) {
      auto arg = args[i];
      auto param = func->params[i];
      int state = cfunc->shape_func_param_states[i]->value;
      if (arg.as<TensorValueNode>()) {
        if (state & kNeedInputData) {
          fset_input(arg_counter++, arg, false);
        }
        if (state & kNeedInputShape) {
          fset_input(arg_counter++, arg, true);
        }
      } else {
        const TupleValueNode* tuple = arg.as<TupleValueNode>();
        CHECK(tuple != nullptr);
        if (state & kNeedInputData) {
          for (size_t i = 0; i < tuple->fields.size(); ++i) {
            fset_input(arg_counter++, tuple->fields[i], false);
          }
        }
        if (state & kNeedInputShape) {
          for (size_t i = 0; i < tuple->fields.size(); ++i) {
            fset_input(arg_counter++, tuple->fields[i], true);
          }
        }
      }
    }
    CHECK_EQ(arg_counter, cfunc->inputs.size())
      << "Shape function input sizes mismatch";

    auto fset_shape_output = [&](size_t i, Type val_type) {
        // TODO(@icemelon): allow recursive tuple
        const TensorTypeNode* rtype = val_type.as<TensorTypeNode>();
        CHECK(rtype != nullptr);
        int64_t ndim = rtype->shape.size();
        auto arr = NDArray::Empty({ndim}, DataType::Int(64), cpu_ctx);
        outputs[i] = arr;
        setter(arg_counter + i, arr);
    };

    auto ret_type = func->body->checked_type();
    size_t out_cnt = 0;
    if (auto rtype = ret_type.as<TupleTypeNode>()) {
      out_cnt = rtype->fields.size();
      for (size_t i = 0; i < out_cnt; ++i) {
        fset_shape_output(i, rtype->fields[i]);
      }
    } else {
      out_cnt = 1;
      auto tt = Downcast<TensorType>(ret_type);
      fset_shape_output(0, tt);
    }
    CHECK_EQ(cfunc->outputs.size(), out_cnt)
      << "Shape function output sizes mismatch";

    PackedFunc shape_func;
    TVMRetValue rv;
    if (const auto* f = runtime::Registry::Get("relay.backend.build")) {
      tvm::runtime::Module m = (*f)(cfunc->funcs, cfunc->target);
      shape_func = m.GetFunction(cfunc->func_name);
    } else {
      LOG(FATAL) << "relay.backend.build is not registered";
    }
    shape_func.CallPacked(TVMArgs(values.data(), codes.data(), arity), &rv);

    // Get output shapes
    Array<Shape> out_shapes;
    for (auto out_tensor : outputs) {
      int64_t* shape_data = reinterpret_cast<int64_t*>(out_tensor->data);
      Shape out_shape;
      for (int i = 0; i < out_tensor->shape[0]; ++i) {
        out_shape.push_back(tvm::Integer(shape_data[i]));
      }
      out_shapes.push_back(out_shape);
    }
    return out_shapes;
  }

};
}  // namespace relay
}  // namespace tvm
