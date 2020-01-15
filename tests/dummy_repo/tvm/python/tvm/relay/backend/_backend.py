"""The interface of expr function exposed from C++."""
from __future__ import absolute_import

from ... import build_module as _build
from ... import container as _container
from ..._ffi.function import _init_api, register_func


@register_func("relay.backend.lower")
def lower(sch, inputs, func_name, source_func):
    import traceback
    # pylint: disable=broad-except
    try:
        f = _build.lower(sch, inputs, name=func_name)
        # logging.debug("lower function %s", func_name)
        # logging.debug("%s", _build.lower(sch, inputs, simple_mode=True))
    except Exception:
        msg = traceback.format_exc()
        msg += "Error during compile function\n"
        msg += "-----------------------------\n"
        msg += source_func.astext()
        raise RuntimeError(msg)
    return f if isinstance(
        f, (_container.Array, tuple, list)) else [f]
