import logging
import multiprocessing
import time

from random import randrange

import numpy as np

from .. import expr, ir_pass

def get_const_int(exp):
    """Verifies expr is integer and get the constant value.

    Parameters
    ----------
    exp : tvm.Expr or int
        The input expression.

    Returns
    -------
    out_value : int
        The output.
    """
    if isinstance(exp, int):
        return exp
    if not isinstance(exp, (expr.IntImm, expr.UIntImm)):
        exp = ir_pass.Simplify(exp)
    if not isinstance(exp, (expr.IntImm, expr.UIntImm)):
        raise ValueError("Expect value to be constant int")
    return exp.value


def get_const_tuple(in_tuple):
    """Verifies input tuple is IntImm or Var, returns tuple of int or Var.

    Parameters
    ----------
    in_tuple : tuple of Expr
        The input.

    Returns
    -------
    out_tuple : tuple of int
        The output.
    """
    ret = []
    for elem in in_tuple:
        if isinstance(elem, expr.Var):
            ret.append(elem)
        elif not isinstance(elem, (expr.IntImm, expr.UIntImm, int)):
            elem = ir_pass.Simplify(elem)
            if not isinstance(elem, (expr.IntImm, expr.UIntImm)):
                ret.append(elem)
        else:
            ret.append(get_const_int(elem))
    return tuple(ret)
