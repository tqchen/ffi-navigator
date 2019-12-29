import textwrap
from ffi_navigator import pattern, lsp


def test_find_cc_register_packed():
    source = """
    TVM_REGISTER_GLOBAL("test.xyz")
    .set_body(TestXYZ)

    /*
     * Part of comment.
     * TVM_REGISTER_GLOBAL("test.xyz")
     * .set_body(TestXYZ)
     /
    REGISTER_MAKE(LetStmt)

    void Test() {
      auto f = GetPackedFunc("test.xyz1")
    }

    """
    items = pattern.find_cc_register_packed("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert items[0].full_name == "test.xyz"
    items = pattern.find_cc_register_packed("api_ir.cc", " REGISTER_MAKE(LetStmt)")
    assert len(items) == 1

    items = pattern.find_cc_get_packed("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert items[0].full_name == "test.xyz1"


def test_find_cc_decl_object():
    source = """
    class GlobalVarNode {
     public:
      static constexpr const char* _type_key = "relay.GlobalVar"
    };
    """
    items = pattern.find_cc_decl_object("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert items[0].full_name == "relay.GlobalVar"


def test_find_py_register_packed():
    source = """
    @register_func
    def test_xyz():
        pass

    @_reg.register_func("test.abc")
    def test_xyz():
        pass

    _reg.register_func("test", myfunc)
    """
    items = pattern.find_py_register_packed("xyz.cc", textwrap.dedent(source))
    assert len(items) == 3
    assert items[0].py_reg_func == "register_func"
    assert items[0].full_name == "test_xyz"
    assert items[1].py_reg_func == "_reg.register_func"
    assert items[1].full_name == "test.abc"
    assert items[2].full_name == "test"


def test_find_py_register_object():
    source = """
    @register_relay_node
    class GlobalVar(Node):
        pass

    @_reg.register_object("test.ABC")
    class ABC(ObjectBase):
        pass
    """
    items = pattern.find_py_register_object("xyz.py", textwrap.dedent(source))
    assert len(items) == 2
    assert items[0].py_reg_func == "register_relay_node"
    assert items[0].full_name == "relay.GlobalVar"
    assert items[1].py_reg_func == "_reg.register_object"
    assert items[1].full_name == "test.ABC"


def test_find_py_imports():
    source = """
    from . import expr
    from . import make as _make, data
    """
    items = pattern.find_py_imports(textwrap.dedent(source))
    assert len(items) == 3
    assert items[0].from_mod == "."
    assert items[0].import_name == "expr"
    assert items[0].alias is None
    assert items[1].from_mod == "."
    assert items[1].import_name == "make"
    assert items[1].alias == "_make"
    assert items[2].from_mod == "."
    assert items[2].import_name == "data"
    assert items[2].alias == None

def test_find_py_init_api():
    source = """
    _init_api("relay.expr")
    """
    items = pattern.find_py_init_api(textwrap.dedent(source))
    assert items[0] == "relay.expr"


def test_extract_symbol():
    source = """
    self.f(_make.Let)

    @register_relay_node
    class GlobalVar(Node)
    """
    pos = lsp.Position(line=1, character=13)
    expr = pattern.extract_symbol(textwrap.dedent(source), pos)
    assert isinstance(expr, pattern.SymExpr)
    assert expr.value == "_make.Let"

    pos = lsp.Position(line=4, character=10)
    expr = pattern.extract_symbol(textwrap.dedent(source), pos)
    assert isinstance(expr, pattern.SymRegObject)
    assert expr.value == "relay.GlobalVar"

    source = """
    auto* pf = GetPackedFunc("test.data")

    class GlobalVarNode {
     public:
      static constexpr const char* _type_key = "relay.GlobalVar"
    };
    """
    pos = lsp.Position(line=1, character=35)
    expr = pattern.extract_symbol(textwrap.dedent(source), pos)
    assert isinstance(expr, pattern.SymGetPackedFunc)
    assert expr.value == "test.data"

    pos = lsp.Position(line=5, character=48)
    expr = pattern.extract_symbol(textwrap.dedent(source), pos)
    assert isinstance(expr, pattern.SymDeclObject)
    assert expr.value == "relay.GlobalVar"


def test_search_symbol():
    source = """
    self.f(_make.Let, data)
    a = [_make, "_make.Let"]
    b = _make+ 1
    """
    res = pattern.search_symbol(textwrap.dedent(source), ["_make.Let"])
    assert(len(res)) == 1
    assert(res[0].start.line == 1)

    res = pattern.search_symbol(textwrap.dedent(source), ["_make"])
    assert(len(res)) == 3
    assert(res[0].start.line == 1)

    res = pattern.search_symbol(textwrap.dedent(source), ["\"_make.Let\""])
    assert(len(res)) == 1



if __name__ == "__main__":
    test_find_py_imports()
    test_find_py_register_packed()
    test_find_cc_register_packed()
    test_find_cc_decl_object()
    test_find_py_register_object()
    test_find_py_init_api()
    test_extract_symbol()
    test_search_symbol()
