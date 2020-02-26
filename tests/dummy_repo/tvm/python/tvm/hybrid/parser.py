"""Hybrid Script Parser"""

import ast
import operator
import logging
import sys
import types
import numbers

from enum import Enum

from .util import _internal_assert
from . import calls
from . import util
from .preprocessor import determine_variable_usage
from ..api import all as _all
from ..api import any as _any

from ..container import Array
from ..tensor import Tensor, Operation
from .. import _api_internal as _tvm_internal
from .. import expr as _expr
from .. import make as _make
from .. import api  as _api
from .. import ir_pass as _ir_pass

class HybridParser(ast.NodeVisitor):
    def visit_Assign(self, node):
        rhs = self.visit(node.value)
        if isinstance(rhs, Operation):
            rmap = {}
            _internal_assert(len(node.targets) == rhs.num_outputs, \
                             "Unable to detuple the outs to targets")
            for i in range(rhs.num_outputs):
                _internal_assert(isinstance(node.targets[i], ast.Name),
                                 "You should bind a pure name to the tensors")
                self.add_symbol(node.targets[i].id, Symbol.GlobalBuffer, rhs.output(i))
                rmap[rhs.outputs[i].op] = rhs.output(i)
            return util.replace_io(rhs.body, rmap)

        _internal_assert(len(node.targets) == 1, "So far only one-valued assignment is supported!")
        lhs = node.targets[0]
        if isinstance(rhs, _expr.Expr):
            rhs = _ir_pass.Simplify(rhs)
        if isinstance(lhs, ast.Name):
            #TODO: support defined intermediate buffer later
            lhs_ = lhs
            lhs = lhs.id
            if lhs in self.symbols.keys():
                ty, _ = self.symbols[lhs]
                _internal_assert(ty != Symbol.LoopVar, \
                                 "Loop variable cannot be overwritten!")
            decl, _, rw = self.usage[lhs]
            if decl == lhs_:
                _internal_assert(lhs not in self.symbols.keys(),
                                 "This value should not be defined before this point!")
                if isinstance(rhs, tuple):
                    shape, dtype, scope = rhs
                    ph = _api.placeholder(shape, dtype=dtype, name=lhs)
                    self.add_symbol(lhs, getattr(Symbol, scope.title() + "Buffer"), ph)
                    if scope == 'output':
                        self.outputs.append(lhs)
                    return util.make_nop()
                if isinstance(rhs, util.halide_imm_types) and ast.Store not in rw:
                    self.add_symbol(lhs, Symbol.ConstVar, rhs)
                else:
                    _internal_assert(self.device == 0,
                                     "Single variable not supported in devices' side!\n" + \
                                     "If you are using GPU, please allocate a 'local' spad " + \
                                     "outside the bind body")
                    ph = _api.placeholder((1, ), dtype=rhs.dtype, name=lhs)
                    self.add_symbol(lhs, Symbol.BufferVar, ph)
            lhs = self.visit(lhs_)
            if lhs is not None:
                buf, args = lhs
                return _make.Provide(buf.op, 0, rhs, args)
            return util.make_nop()

        lhs, args = self.visit(lhs)
        _internal_assert(isinstance(lhs, Tensor), \
                         "An array access's LHS is expected to be a expr.Call!")
        res = _make.Provide(lhs.op, lhs.value_index, rhs, args)
        return res

    def visit_AugAssign(self, node):
        buf = self.visit(node.target)
        rhs = self.visit(node.value)
        if isinstance(buf, tuple):
            _internal_assert(len(buf) == 2, "LHS is supposed to be (buf, args)!")
            buf, args = buf
        else:
            args = [_api.const(0, 'int32')]
        _internal_assert(isinstance(buf, Tensor), "LHS is supposed to be Tensor!")

        read = _make.Call(buf.dtype, buf.name, args, _expr.Call.Halide, buf.op, buf.value_index)
        value = HybridParser._binop_maker[type(node.op)](read, rhs)

        return _make.Provide(buf.op, 0, value, args)
