#include <torch/csrc/python_headers.h>
#include <sys/types.h>
#include <unordered_map>
#include <cstdlib>
#include <libshm.h>
#include <TH/TH.h>
#include <c10/util/Logging.h>
#include <ATen/ATen.h>
#include <ATen/ExpandUtils.h>
#include <ATen/dlpack.h>
#include <ATen/DLConvertor.h>
#include <ATen/Parallel.h>
#include <ATen/Utils.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

PyObject *THPModule_setQEngine(PyObject */* unused */, PyObject *arg)
{
  THPUtils_assert(THPUtils_checkLong(arg), "set_qengine expects an int, "
          "but got %s", THPUtils_typename(arg));
  auto qengine = static_cast<int>(THPUtils_unpackLong(arg));
  at::globalContext().setQEngine(static_cast<at::QEngine>(qengine));
  Py_RETURN_NONE;
}

PyObject *THPModule_qEngine(PyObject */* unused */)
{
  return THPUtils_packInt64(static_cast<int>(at::globalContext().qEngine()));
}

PyObject *THPModule_supportedQEngines(PyObject */* unused */)
{
  auto qengines = at::globalContext().supportedQEngines();
  auto list = THPObjectPtr(PyList_New(qengines.size()));
  for (size_t i = 0; i < qengines.size(); ++i) {
    PyObject *i64 = THPUtils_packInt64(static_cast<int>(qengines[i]));
    if (!i64) {
      throw python_error();
    }
    PyList_SET_ITEM(list.get(), i, i64);
  }
  return list.release();
}

//NOLINTNEXTLINE(cppcoreguidelines-avoid-c-arrays, modernize-avoid-c-arrays)
static PyMethodDef TorchMethods[] = {
  {"_get_qengine", (PyCFunction)THPModule_qEngine, METH_NOARGS, nullptr},
  {"_set_qengine", (PyCFunction)THPModule_setQEngine, METH_O, nullptr},
  {"_supported_qengines", (PyCFunction)THPModule_supportedQEngines, METH_NOARGS, nullptr},
  {nullptr, nullptr, 0, nullptr}
};
