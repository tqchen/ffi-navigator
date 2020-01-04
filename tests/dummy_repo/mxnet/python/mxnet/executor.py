class Executor(object):
    def __init__(self, handle, symbol, ctx, grad_req, group2ctx):
        if not isinstance(handle, ExecutorHandle):
            raise TypeError("Handle type error")
        self.handle = handle
        self.arg_arrays = []
        self.grad_arrays = []
        self.aux_arrays = []
        self.outputs = self._get_outputs()
        self._symbol = copy.deepcopy(symbol)
        self._optimized_symbol = None
        self._arg_dict = None
        self._grad_dict = None
        self._aux_dict = None
        self._output_dict = None
        self._monitor_callback = None
        self._ctx = copy.deepcopy(ctx)
        self._grad_req = copy.deepcopy(grad_req)
        self._group2ctx = copy.deepcopy(group2ctx)

    def __del__(self):
        check_call(_LIB.MXExecutorFree(self.handle))

    @staticmethod
    def _get_dict(names, ndarrays):
        """Get the dictionary given name and ndarray pairs."""
        nset = set()
        for nm in names:
            if nm in nset:
                raise ValueError('Duplicate names detected, %s' % str(names))
            nset.add(nm)
        return dict(zip(names, ndarrays))

    def _get_outputs(self):
        out_size = mx_uint()
        handles = ctypes.POINTER(NDArrayHandle)()
        check_call(_LIB.MXExecutorOutputs(self.handle,
                                          ctypes.byref(out_size), ctypes.byref(handles)))
        num_output = out_size.value
        outputs = [_ndarray_cls(NDArrayHandle(handles[i])) for i in range(num_output)]
        return outputs

    def forward(self, is_train=False, **kwargs):
        if len(kwargs) != 0:
            arg_dict = self.arg_dict
            for name, array in kwargs.items():
                if not isinstance(array, (NDArray, np.ndarray)):
                    raise ValueError('only accept keyword argument of NDArrays and numpy.ndarray')
                if name not in arg_dict:
                    raise TypeError('Unknown argument %s' % name)
                if arg_dict[name].shape != array.shape:
                    raise ValueError('Shape not match! Argument %s, need: %s, received: %s'
                                     %(name, str(arg_dict[name].shape), str(array.shape)))
                arg_dict[name][:] = array

        check_call(_LIB.MXExecutorForward(
            self.handle,
            ctypes.c_int(int(is_train))))
        self.outputs = self._get_outputs()
        return self.outputs
