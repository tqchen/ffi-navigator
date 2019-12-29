"""Simple pattern detection tool using regex"""
import re
import attr
from typing import Optional
from .lsp import Range, Position, Location

# We use simple regular expression matching
# Note that such match may not take account into fact like
# the code is in a multiline comment block, but such case is rare
@attr.s
class PackedFuncDef:
    """Packed function declaration"""
    path : str = attr.ib()
    full_name : str = attr.ib()
    range: Range = attr.ib()
    py_reg_func: Optional[str] = attr.ib(default=None)


@attr.s
class PackedFuncRef:
    """Packed function reference"""
    path : str = attr.ib()
    full_name : str = attr.ib()
    range: Range = attr.ib()


@attr.s
class ObjectDef:
    """Packed function reference"""
    path : str = attr.ib()
    full_name : str = attr.ib()
    range: Range = attr.ib()


@attr.s
class ObjectReg:
    """Packed function reference"""
    path : str = attr.ib()
    full_name : str = attr.ib()
    range: Range = attr.ib()
    py_reg_func: Optional[str] = attr.ib(default=None)


@attr.s
class PyImport:
    """Python import"""
    from_mod : Optional[str] = attr.ib()
    import_name : str = attr.ib()
    alias : Optional[str] = attr.ib()


def find_register_packed_macro(path, source, macro_suffix, packed_prefix):
    rexpr = re.compile(r"\s*REGISTER_" + macro_suffix + r"[^\(]*\((?P<name>[^\),]+)")
    # Special handling of api registery
    # consider not use the macro later
    results = []
    for line, content in enumerate(source):
        match = rexpr.match(content)
        if match:
            start, end = match.span()
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            decl = PackedFuncDef(
                path=path, full_name=packed_prefix+match.group("name"),
                range=Range(start_pos, end_pos))
            results.append(decl)
    return results


RE_CC_REGISTER_PACKED = re.compile(r"\s*(TVM_REGISTER_GLOBAL|TVM_REGISTER_API)\(\"(?P<full_name>[^\"]+)\"\)")

def find_cc_register_packed(path, source):
    """Find C++ packed function registrations."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_CC_REGISTER_PACKED.match(content)
        if match:
            start, end = match.span("full_name")
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            decl = PackedFuncDef(
                path=path, full_name=match.group("full_name"),
                range=Range(start_pos, end_pos))
            results.append(decl)
    if path.endswith("api_ir.cc"):
        results += find_register_packed_macro(path, source, "MAKE", "make.")
    if path.endswith("api_pass.cc"):
        results += find_register_packed_macro(path, source, "PASS", "ir_pass.")
    return results


RE_CC_GET_PACKED = re.compile(r"(GetPackedFunc|runtime::Registry::Get)\(\"(?P<full_name>[^\"]+)\"\)")

def find_cc_get_packed(path, source):
    """Find C++ packed function registrations."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        start_pos = 0
        while True:
            match = RE_CC_GET_PACKED.search(content, start_pos)
            if not match:
                break
            start, end = match.span("full_name")
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            decl = PackedFuncRef(
                path=path, full_name=match.group("full_name"),
                range=Range(start_pos, end_pos))
            results.append(decl)
            start_pos = end
    return results

RE_CC_DECL_OBJECT = re.compile(r"const\s+char\s*\*\s+_type_key\s*=\s*\"(?P<full_name>[^\"]+)\"")

def find_cc_decl_object(path, source):
    """Find C++ packed function registrations."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_CC_DECL_OBJECT.search(content)
        if match:
            start, end = match.span()
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            decl = ObjectDef(
                path=path,
                full_name=match.group("full_name"),
                range=Range(start_pos, end_pos))
            results.append(decl)
    return results


RE_PY_REGISTER_PACKED = re.compile(
    r"@?(?P<reg>([a-zA-Z_]?[a-zA-Z_0-9.]*.)?register_func)" +
    r"((\(\"(?P<full_name>[^\"]+)\")|(\s*\Z))")
RE_PY_FUNC_DEF = re.compile(r"def\s+(?P<full_name>[a-zA-Z_0-9]+)\(")

def find_py_register_packed(path, source):
    """Discover python registration information."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_PY_REGISTER_PACKED.match(content)
        if match:
            start, end = match.span()
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            reg_func = match.group("reg")
            full_name = match.group("full_name")
            if not full_name and line + 1 < len(source):
                match_name = RE_PY_FUNC_DEF.match(source[line + 1])
                if match_name:
                    full_name = match_name.group("full_name")
            if full_name:
                decl = PackedFuncDef(
                    path=path, full_name=full_name,
                    range=Range(start_pos, end_pos),
                    py_reg_func=reg_func)
                results.append(decl)
    return results


RE_PY_REGISTER_OBJECT = re.compile(
    r"@(?P<reg>([a-zA-Z_]?[a-zA-Z_0-9.]*.)?(register_object|register_node|register_relay_node))" +
    r"(\(\"(?P<full_name>[^\"]+)?\"\))?")
RE_PY_CLASS_DEF = re.compile(r"class\s+(?P<full_name>[a-zA-Z_0-9]+)\(")

def find_py_register_object(path, source):
    """Discover python registration information."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_PY_REGISTER_OBJECT.match(content)
        if match:
            start, end = match.span()
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            reg_func = match.group("reg")
            full_name = match.group("full_name")
            if not full_name and line + 1 < len(source):
                match_name = RE_PY_CLASS_DEF.match(source[line + 1])
                if match_name:
                    full_name = match_name.group("full_name")
            if full_name:
                if match.group("reg").endswith("register_relay_node"):
                    full_name = "relay." + full_name
                decl = ObjectReg(
                    path=path, full_name=full_name,
                    range=Range(start_pos, end_pos),
                    py_reg_func=reg_func)
                results.append(decl)
    return results


RE_PY_IMPORT_PREFIX = re.compile(r"\s*from\s+(?P<mod>[^\s]+)\s+import")
RE_PY_IMPORT_ITEM = re.compile(r"\s+(?P<name>[^\s]+)(\s+as\s+(?P<alias>[^\s]+))?")


def find_py_imports(source):
    """Discover python import information."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        prefix = RE_PY_IMPORT_PREFIX.match(content)
        if prefix:
            from_mod = prefix.group("mod")
            for item in content[prefix.end():].split(","):
                match = RE_PY_IMPORT_ITEM.match(item)
                if match:
                    results.append(PyImport(from_mod=from_mod,
                                            import_name=match.group("name"),
                                            alias=match.group("alias")))
    return results


RE_PY_INIT_API = re.compile(r"_init_api\(\"(?P<api_name>[^\"]+)\"")

def find_py_init_api(source):
    """Find _init_api."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_PY_INIT_API.match(content)
        if match:
            results.append(match.group("api_name"))
    return results

class Sym:
    pass

@attr.s
class SymExpr(Sym):
    value: str = attr.ib()

@attr.s
class SymGetPackedFunc(Sym):
    value: str = attr.ib()

@attr.s
class SymRegPackedFunc(Sym):
    value: str = attr.ib()

@attr.s
class SymRegObject(Sym):
    value: str = attr.ib()

@attr.s
class SymDeclObject(Sym):
    value: str = attr.ib()


RE_PY_NAMESPACE_PREFIX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_.]+\Z")
RE_PY_VAR_NAME = re.compile(r"[a-zA-Z0-9_.]+")
RE_CC_GET_PACKED_PREFIX = re.compile(r"(GetPackedFunc|runtime::Registry::Get)\(\"\Z")
RE_CC_REG_PACKED_PREFIX = re.compile(r"\s*(TVM_REGISTER_GLOBAL|TVM_REGISTER_API)\(\"\Z")
RE_PY_REG_PACKED_PREFIX = re.compile(r"@(?P<reg>[a-zA-Z_]?[a-zA-Z_0-9.]*register_func)\(\"\Z")
RE_CC_DECL_TYPE_KEY_PREFIX = re.compile(r"char\s*\*\s*_type_key\s*=\s*\"\Z")
RE_PY_CLASS_PREFIX = re.compile(r"\s*class\s+\Z")


def extract_symbol(source, pos: Position):
    """Find the complete expression, include namespace prefix"""
    source = source.split("\n") if isinstance(source, str) else source
    content = source[pos.line]
    mprefix = RE_PY_NAMESPACE_PREFIX.search(content, 0, pos.character)
    start = mprefix.start() if mprefix else pos.character
    mvar = RE_PY_VAR_NAME.match(content, pos.character)
    end = mvar.end() if mvar else pos.character
    value = content[start:end]

    if RE_PY_CLASS_PREFIX.match(content, 0, start) and pos.line != 0:
        match = RE_PY_REGISTER_OBJECT.match(source[pos.line - 1])
        if match:
            full_name = match.group("full_name")
            full_name = value if full_name is None else full_name
            if match.group("reg").endswith("register_relay_node"):
                full_name = "relay." + full_name
            return SymRegObject(value=full_name)

    if end < len(content) and content[end] == "\"":
        if RE_CC_GET_PACKED_PREFIX.search(content, 0, start):
            return SymGetPackedFunc(value)
        if RE_CC_REG_PACKED_PREFIX.search(content, 0, start):
            return SymRegPackedFunc(value=value)
        if RE_PY_REG_PACKED_PREFIX.search(content, 0, start):
            return SymRegPackedFunc(value=value)
        if RE_CC_DECL_TYPE_KEY_PREFIX.search(content, 0, start):
            return SymDeclObject(value=value)
        return None

    return SymExpr(value)


RE_PY_DELIM = r"(\s|[.,\(\)\[\]{}:=\+\-\*]|\Z)+"

def search_symbol(source,  symbols):
    """Find the complete expression, include namespace prefix"""
    source = source.split("\n") if isinstance(source, str) else source
    rexpr = RE_PY_DELIM + "(?P<name>("
    rexpr += "|".join([re.escape(sym) for sym in symbols]) + "))"
    rexpr += RE_PY_DELIM
    rexpr = re.compile(rexpr)
    results = []

    for line, content in enumerate(source):
        match = rexpr.search(content)
        if match:
            start, end = match.span("name")
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            results.append(Range(start_pos, end_pos))
    return results
