from __future__ import absolute_import
from numbers import Number as _Number

import numpy as _np
from .base import RelayNode, register_relay_node
from . import _make
from . import _expr
from . import ty as _ty
from .._ffi import base as _base
from .. import nd as _nd
from .. import convert
from ..ndarray import NDArray


@register_relay_node
class Constant(Expr):
    """A constant expression in Relay.

    Parameters
    ----------
    data : tvm.nd.NDArray
        The data content of the constant expression.
    """
    def __init__(self, data):
        self.__init_handle_by_constructor__(_make.Constant, data)
