#include <torch/csrc/autograd/python_function.h>
#include <torch/csrc/python_headers.h>
#include <structmember.h>
#include <unordered_map>
#include <unordered_set>
#include <exception>
#include <ATen/ATen.h>


static struct PyMethodDef THPFunction_methods[] = {
  {(char*)"apply", (PyCFunction)THPFunction_apply, METH_CLASS | METH_VARARGS, nullptr},
  {(char*)"_do_forward", (PyCFunction)THPFunction_do_forward, METH_VARARGS, nullptr},
  {(char*)"_do_backward", (PyCFunction)THPFunction_do_backward, METH_VARARGS, nullptr},
  {(char*)"_register_hook_dict", (PyCFunction)THPFunction__register_hook_dict, METH_O, nullptr},
  {(char*)"register_hook", (PyCFunction)THPFunction_register_hook, METH_O, nullptr},
  {nullptr}
};
