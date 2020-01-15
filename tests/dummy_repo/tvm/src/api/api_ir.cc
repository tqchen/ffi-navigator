#include <tvm/expr.h>
#include <tvm/ir.h>
#include <tvm/runtime/registry.h>
#include <tvm/packed_func_ext.h>

#include <tvm/expr_operator.h>

namespace tvm {
namespace ir {

#define REGISTER_MAKE(Node)
  TVM_REGISTER_GLOBAL("make." #Node)
  .set_body_typed(Node::make);

REGISTER_MAKE(ProducerConsumer);
REGISTER_MAKE(LetStmt);

} // namespace ir
}
