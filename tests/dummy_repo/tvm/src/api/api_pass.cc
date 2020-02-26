#include <tvm/expr.h>
#include <tvm/ir.h>
#include <tvm/attrs.h>
#include <tvm/ir_pass.h>
#include <tvm/ir_functor_ext.h>
#include <tvm/api_registry.h>

namespace tvm {
namespace ir {

TVM_REGISTER_API("ir_pass.Simplify")
.set_body([](TVMArgs args, TVMRetValue *ret) {
    if (args[0].IsObjectRef<Stmt>()) {
      if (args.size() > 1) {
        *ret = Simplify(args[0].operator Stmt(), args[1]);
      } else {
        *ret = Simplify(args[0].operator Stmt());
      }
    } else {
      if (args.size() > 1) {
        *ret = Simplify(args[0].operator Expr(), args[1]);
      } else {
        *ret = Simplify(args[0].operator Expr());
      }
    }
  });
}  // namespace ir
}  // namespace tvm
