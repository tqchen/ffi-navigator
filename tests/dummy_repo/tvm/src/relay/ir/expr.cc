#include <tvm/relay/expr.h>

namespace tvm {
namespace relay {

using tvm::IRPrinter;
using namespace tvm::runtime;

Constant ConstantNode::make(runtime::NDArray data) {
  ObjectPtr<ConstantNode> n = make_object<ConstantNode>();
  n->data = std::move(data);
  return Constant(n);
}

TVM_REGISTER_NODE_TYPE(ConstantNode);

TVM_REGISTER_API("relay._make.Constant")
.set_body_typed(ConstantNode::make);

} // namespace relay
}
