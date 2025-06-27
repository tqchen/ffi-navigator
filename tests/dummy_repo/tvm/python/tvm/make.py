"""namespace of IR node builder make function

This namespace is used for developers. While you do not see any declarations.
The functions are automatically exported from C++ side via PackedFunc.

Each api is a PackedFunc that can be called in a positional argument manner.
You can use make function to build the IR node.
"""
from __future__ import absolute_import as _abs
import tvm._ffi

# test reference in the same file.
def make_ProducerConsumer(is_prod, body):
    return ProducerConsumer(is_prod, body)


tvm.ffi._init_api("tvm.make")
