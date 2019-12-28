import textwrap
from ffi_navigator import pattern, lsp

def test_find_register_packed_cc():
    source = """
    TVM_REGISTER_GLOBAL("test.xyz")
    .set_body(TestXYZ)

    /*
     * Part of comment.
     * TVM_REGISTER_GLOBAL("test.xyz")
     * .set_body(TestXYZ)
     /
    REGISTER_MAKE(LetStmt)
    """
    items = pattern.find_register_packed("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert items[0].full_name == "test.xyz"
    items = pattern.find_register_packed("api_ir.cc", " REGISTER_MAKE(LetStmt)")
    assert len(items) == 1

def test_find_pyimports():
    source = """
    from . import expr
    from . import make as _make
    """
    items = pattern.find_pyimports(textwrap.dedent(source))
    assert len(items) == 2
    assert items[0].from_mod == "."
    assert items[0].import_name == "expr"
    assert items[0].alias is None
    assert items[1].from_mod == "."
    assert items[1].import_name == "make"
    assert items[1].alias == "_make"

def test_find_init_api_py():
    source = """
    _init_api("relay.expr")
    """
    items = pattern.find_init_api(textwrap.dedent(source))
    assert items[0] == "relay.expr"


def test_extract_expr():
    source = """
    self.f(_make.Let)
    """
    pos = lsp.Position(line=1, character=13)
    expr = pattern.extract_expr(textwrap.dedent(source), pos)
    assert expr == "_make.Let"

if __name__ == "__main__":
    test_find_pyimports()
    test_find_register_packed_cc()
    test_find_init_api_py()
    test_extract_expr()
