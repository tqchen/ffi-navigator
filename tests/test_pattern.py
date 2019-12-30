import textwrap
from ffi_navigator import pattern, lsp

def test_cc_find_packed():
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

    finder = pattern.macro_matcher(
        ["TVM_REGISTER_GLOBAL", "TVM_REGISTER_API"],
        lambda skey, path, rg, _: pattern.Def(skey, path, rg))
    items = finder("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert isinstance(items[0], pattern.Def)
    assert items[0].key == "test.xyz"

    finder = pattern.func_get_searcher(
        ["GetPackedFunc"],
        lambda skey, path, rg, _: pattern.Ref(skey, path, rg))
    items = finder("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert items[0].key == "test.xyz1"


def test_find_cc_decl_object():
    source = """
    class GlobalVarNode {
     public:
      static constexpr const char* _type_key = "relay.GlobalVar"
    };
    """
    finder = pattern.re_matcher(
        r"\s*static\s+constexpr\sconst\s+char\s*\*\s+_type_key\s*=\s*\"(?P<key>[^\"]+)\"",
        lambda match, path, rg:
        pattern.Def(key="t:"+match.group("key"), path=path, range=rg))
    items = finder("xyz.cc", textwrap.dedent(source))
    assert len(items) == 1
    assert items[0].key == "t:relay.GlobalVar"


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
    finder = pattern.decorator_matcher(
        ["register_func"], "def",
        lambda key, path, rg, _: pattern.Def(key=key, path=path, range=rg))
    items = finder("xyz.cc", textwrap.dedent(source))
    assert len(items) == 3
    assert items[0].key == "test_xyz"
    assert items[1].key == "test.abc"
    assert items[2].key == "test"


def test_find_py_register_object():
    source = """
    @register_relay_node
    class GlobalVar(Node):
        pass

    @_reg.register_object("test.ABC")
    class ABC(ObjectBase):
        pass
    """
    finder = pattern.decorator_matcher(
        ["register_object", "register_relay_node"], "class",
        lambda key, path, rg, reg:
        pattern.Def(key="t:relay."+key, path=path, range=rg)
        if reg.endswith("relay_node")
        else pattern.Def(key="t:"+key, path=path, range=rg))
    items = finder("xyz.cc", textwrap.dedent(source))
    assert len(items) == 2
    assert items[0].key == "t:relay.GlobalVar"
    assert items[1].key == "t:test.ABC"


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
    test_cc_find_packed()
    test_find_cc_decl_object()
    test_find_py_register_packed()
    test_find_py_register_object()
    test_search_symbol()
