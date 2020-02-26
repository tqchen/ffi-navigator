from __future__ import absolute_import as _abs

from . import api as _api
from . import stmt as _stmt
from . import expr as _expr
from . import make as _make
from . import ir_pass as _pass
from . import container as _container
from ._ffi.base import string_types
from ._ffi.node import NodeGeneric
from ._ffi.runtime_ctypes import TVMType
from .expr import Call as _Call

class IRBuilder(object):
    def for_range(self, begin, end, name="i", dtype="int32", for_type="serial"):
        if name == 'i':
            name = chr(ord(name) + self.nidx) if self.nidx < 3 else name + "_" + str(self.nidx - 3)
            self.nidx += 1
        self._seq_stack.append([])
        loop_var = _api.var(name, dtype=dtype)
        extent = end if begin == 0 else _pass.Simplify(end - begin)
        def _exit_cb():
            if for_type == "serial":
                for_type_id = 0
            elif for_type == "parallel":
                for_type_id = 1
            elif for_type == "vectorize":
                for_type_id = 2
            elif for_type == "unroll":
                for_type_id = 3
            else:
                raise ValueError("Unknown for_type")
            self.emit(_make.For(
                loop_var, begin, extent, for_type_id, 0, self._pop_seq()))
        return WithScope(loop_var, _exit_cb)
