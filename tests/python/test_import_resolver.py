from ffi_navigator.import_resolver import PyImportResolver
from ffi_navigator.util import is_win

def test_import_resolver():
    if is_win(): return

    doc_expr = """
    from . import make as _make
    """
    doc_init = """
    from . import relay
    """
    doc_relay_init = """
    from .expr import add
    from . import expr
    """
    doc_relay_expr = """
    from . import _expr
    from ._expr import add
    from .._ffi.function import _init_api
    """
    doc_relay_backend_backend = """
    from ... import build_module as _build
    from ... import container as _container
    from ..._ffi.function import _init_api, register_func
    """
    doc_stmt = """
    from . import make as _make
    """
    doc_make = """
    """
    resolver = PyImportResolver()
    resolver.update_doc("/tvm/relay/backend/_backend", doc_relay_backend_backend)
    resolver.update_doc("/tvm/__init__.py", doc_init)
    resolver.update_doc("/tvm/relay/expr.py", doc_expr)
    resolver.update_doc("/tvm/relay/__init__.py", doc_relay_init)
    resolver.update_doc("/tvm/relay/expr.py", doc_relay_expr)
    resolver.update_doc("/tvm/stmt.py", doc_stmt)
    resolver.update_doc("/tvm/make.py", doc_make)
    assert resolver.resolve("/tvm", "relay.add") == ("/tvm/relay/_expr", "add")
    assert resolver.resolve("/tvm/relay", "expr.sub") == ("/tvm/relay/expr", "sub")

    assert resolver.resolve("/tvm/relay/expr", "_init_api") == ("/tvm/_ffi/function", "_init_api")
    assert resolver.resolve("/tvm/stmt", "_make") == ("/tvm/make", None)
    assert resolver.resolve("/tvm/relay/backend/_backend", "_init_api") == (
        "/tvm/_ffi/function", "_init_api")

if __name__ == "__main__":
    test_import_resolver()
