#include "tlang.h"
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <taichi/common/interface.h>
#include <taichi/python/export.h>
#include "svd.h"

void export_lang(py::module &m) {
  m.def("global_var_expr_from_snode", [](SNode *snode) {
    return Expr::make<GlobalVariableExpression>(snode);
  });

}
