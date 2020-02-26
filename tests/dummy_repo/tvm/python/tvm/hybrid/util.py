import ast
import inspect
import logging
import sys
import numpy
from .. import api as _api
from .. import make as _make
from .. import expr as _expr
from .. import stmt as _stmt
from .._ffi.base import numeric_types
from ..tensor import Tensor
from ..container import Array

def replace_io(body, rmap):
    """Replacing tensors usage according to the dict given"""
    from .. import ir_pass

    def replace(op):
        if isinstance(op, _stmt.Provide) and op.func in rmap.keys():
            buf = rmap[op.func]
            return _make.Provide(buf.op, op.value_index, op.value, op.args)
        if isinstance(op, _expr.Call) and  op.func in rmap.keys():
            buf = rmap[op.func]
            return _make.Call(buf.dtype, buf.name, op.args, \
                              _expr.Call.Halide, buf.op, buf.value_index)
        return None

    return ir_pass.IRTransform(body, None, replace, ['Provide', 'Call'])
