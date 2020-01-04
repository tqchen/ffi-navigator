static PyMethodDef torch_functions[] = {
  {"conv1d", (PyCFunction)(void(*)(void))THPVariable_conv1d, METH_VARARGS | METH_KEYWORDS | METH_STATIC, NULL},
  {"conv2d", (PyCFunction)(void(*)(void))THPVariable_conv2d, METH_VARARGS | METH_KEYWORDS | METH_STATIC, NULL},
  {"conv3d", (PyCFunction)(void(*)(void))THPVariable_conv3d, METH_VARARG
  };
