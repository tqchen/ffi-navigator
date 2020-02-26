from __future__ import absolute_import as _abs
from ._ffi.node import NodeBase, register_node
from . import make as _make


class Stmt(NodeBase):
    pass


@register_node
class ProducerConsumer(Stmt):
    """ProducerConsumer node.

    Parameters
    ----------
    func : Operation
        The Operation.

    is_producer : bool
        Whether if the node is producer.

    body : Stmt
        The body statement.
    """
    def __init__(self, func, is_producer, body):
        self.__init_handle_by_constructor__(
            _make.ProducerConsumer, func, is_producer, body)


@register_node
class LetStmt(Stmt):
    """LetStmt node.

    Parameters
    ----------
    var : Var
        The variable in the binding.

    value : Expr
        The value in to be binded.

    body : Stmt
        The body statement.
    """
    def __init__(self, var, value, body):
        self.__init_handle_by_constructor__(
            _make.LetStmt, var, value, body)


class Provide(Stmt):
    """Provide node.

    Parameters
    ----------
    func : Operation
        The operation to create the function.

    value_index : int
        The output value index

    value : Expr
        The value to be stored.

    args : list of Expr
        The index arguments of the Provide.
    """
    def __init__(self, func, value_index, value, args):
        self.__init_handle_by_constructor__(
            _make.Provide, func, value_index, value, args)
