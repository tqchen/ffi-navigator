#include <torch/csrc/autograd/python_engine.h>
#include <torch/csrc/DynamicTypes.h>
#include <torch/csrc/PtrWrapper.h>
#include <torch/csrc/THP.h>
#include <torch/csrc/autograd/edge.h>
#include <torch/csrc/autograd/engine.h>
#include <torch/csrc/autograd/function.h>
#include <torch/csrc/autograd/python_anomaly_mode.h>
#include <torch/csrc/autograd/python_function.h>
#include <pybind11/pybind11.h>


static struct PyMethodDef THPEngine_methods[] = {
  {(char*)"run_backward", (PyCFunction)(void(*)(void))THPEngine_run_backward, METH_VARARGS | METH_KEYWORDS, nullptr},
  {(char*)"queue_callback", (PyCFunction)THPEngine_queue_callback, METH_O, nullptr},
  {(char*)"is_checkpoint_valid", (PyCFunction)THPEngine_is_checkpoint_valid, METH_NOARGS, nullptr},
  {nullptr}
};
