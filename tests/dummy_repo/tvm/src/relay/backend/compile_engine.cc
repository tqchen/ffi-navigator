#include <tvm/schedule.h>
#include <tvm/packed_func_ext.h>
#include <tvm/operation.h>
#include <tvm/runtime/registry.h>
#include <tvm/relay/attrs/device_copy.h>
#include <tvm/relay/analysis.h>
#include <tvm/relay/expr.h>
#include <tvm/relay/expr_functor.h>
#include <tvm/relay/op_attr_types.h>
#include <topi/tags.h>
#include <utility>
#include <limits>
#include <mutex>
#include <functional>
#include <vector>
#include <unordered_map>
#include "../ir/type_functor.h"
#include "compile_engine.h"

namespace tvm {
namespace relay {

class CompileEngineImpl : public CompileEngineNode {
 private:
  // implement lowered func
  CCacheValue LowerInternal(const CCacheKey& key)  {
    std::lock_guard<std::mutex> lock(mutex_);
    CCacheValue value;
    auto it = cache_.find(key);
    if (it != cache_.end()) {
      it->second->use_count += 1;
      if (it->second->cached_func.defined()) return it->second;
      value = it->second;
    } else {
      value = CCacheValue(make_node<CCacheValueNode>());
      value->use_count = 0;
      cache_[key] = value;
    }
    // No need to lower external functions for now. We will invoke the external
    // codegen tool once and lower all functions together.
    if (!key->source_func->UseDefaultCompiler()) {
      auto cache_node = make_node<CachedFuncNode>();
      const auto name_node =
          FunctionGetAttr(key->source_func, attr::kExternalSymbol).as<tvm::ir::StringImm>();
      CHECK(name_node != nullptr) << "External function has not been attached a name yet.";
      cache_node->func_name = name_node->value;
      cache_node->target = tvm::target::ext_dev();
      value->cached_func = CachedFunc(cache_node);
      return value;
    }
    // Enforce use the target.
    With<Target> target_scope(key->target);

    CHECK(!value->cached_func.defined());
    auto spair = CreateSchedule(key->source_func, key->target);
    auto cache_node = make_node<CachedFuncNode>(
        *(spair.second.operator->()));

    // Skip lowering for device copy node.
    const Expr body = (key->source_func)->body;
    if (const CallNode* call_node = body.as<CallNode>()) {
      if (call_node->attrs.as<DeviceCopyAttrs>()) {
        value->cached_func = CachedFunc(cache_node);
        return value;
      }
    }

    cache_node->func_name = GetUniqueName(cache_node->func_name);
    // NOTE: array will copy on write.
    Array<Tensor> all_args = cache_node->inputs;
    for (Tensor arg : cache_node->outputs) {
      all_args.push_back(arg);
    }
    // lower the function
    if (const auto* f = runtime::Registry::Get("relay.backend.lower")) {
      cache_node->funcs = (*f)(
          spair.first, all_args, cache_node->func_name, key->source_func);
    } else {
      tvm::BuildConfig bcfg = BuildConfig::Create();
      std::unordered_map<Tensor, Buffer> binds;
      cache_node->funcs = tvm::lower(spair.first, all_args, cache_node->func_name, binds, bcfg);
    }
    value->cached_func = CachedFunc(cache_node);
    return value;
  }

  PackedFunc JIT(const CCacheKey& key) final {
    CCacheValue value = LowerInternal(key);
    if (value->packed_func != nullptr) return value->packed_func;
    // build the function.
    if (const auto* f = runtime::Registry::Get("relay.backend.build")) {
      tvm::runtime::Module m = (*f)(value->cached_func->funcs, key->target);
      value->packed_func = m.GetFunction(value->cached_func->func_name);
    } else {
      LOG(FATAL) << "relay.backend.build is not registered";
    }
    return value->packed_func;
  }

};
}  // namespace relay
}  // namespace tvm
