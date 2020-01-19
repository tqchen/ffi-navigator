from __future__ import absolute_import as _abs
from ._ffi.node import NodeBase, NodeGeneric, register_node
from ._ffi.runtime_ctypes import TVMType, TypeCode
from . import make as _make
from . import generic as _generic
from . import _api_internal


class Expr(ExprOp, NodeBase):
    """Base class of all tvm Expressions"""
    # In Python3, We have to explicitly tell interpreter to retain __hash__ if we overide __eq__
    # https://docs.python.org/3.1/reference/datamodel.html#object.__hash__
    __hash__ = NodeBase.__hash__


@register_node("Variable")
class Var(Expr):
    """Symbolic variable.

    Parameters
    ----------
    name : str
        The name

    dtype : int
        The data type
    """
    def __init__(self, name, dtype):
        self.__init_handle_by_constructor__(
            _api_internal._Var, name, dtype)
