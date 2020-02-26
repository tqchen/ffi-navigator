#include <tvm/expr.h>
#include <tvm/ir.h>
#include <tvm/tensor.h>
#include <tvm/operation.h>
#include <tvm/buffer.h>
#include <tvm/schedule.h>
#include <tvm/runtime/registry.h>
#include <tvm/packed_func_ext.h>

#include <tvm/build_module.h>
#include <tvm/data_layout.h>


namespace tvm {

TVM_REGISTER_GLOBAL("_min_value")
.set_body_typed(min_value);

}
