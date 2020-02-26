from ._ffi.base import string_types
from ._ffi.object import register_object, Object
from ._ffi.node import register_node, NodeBase
from ._ffi.node import convert_to_node as _convert_to_node
from ._ffi.node_generic import _scalar_type_inference
from ._ffi.function import Function
from ._ffi.function import _init_api, register_func, get_global_func, extract_ext_funcs
from ._ffi.function import convert_to_tvm_func as _convert_tvm_func
from ._ffi.runtime_ctypes import TVMType
from . import _api_internal
from . import make as _make
from . import expr as _expr
from . import tensor as _tensor
from . import schedule as _schedule
from . import container as _container
from . import tag as _tag

int8 = "int8"
int32 = "int32"
float32 = "float32"
handle = "handle"


def min_value(dtype):
    return _api_internal._min_value(dtype)
