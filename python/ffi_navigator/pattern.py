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


RE_PY_REGISTER_PACKED0 = re.compile(r"@?(?P<reg>[a-zA-Z_]?[a-zA-Z_0-9.]*register_func)\(\"(?P<full_name>[^\"]+)\"")
RE_PY_REGISTER_PACKED1 = re.compile(r"@(?P<reg>[a-zA-Z_]?[a-zA-Z_0-9.]*register_func)\s*\Z")
RE_PY_REGISTER_PACKED1_DEF = re.compile(r"def\s+(?P<full_name>[a-zA-Z_0-9]+)\(")

def find_py_register_packed(path, source):
    """Discover python registration information."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match0 = RE_PY_REGISTER_PACKED0.match(content)
        if match0:
            start, end = match0.span()
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            reg_func = match0.group("reg")
            decl = PackedFuncDef(
                path=path, full_name=match0.group("full_name"),
                range=Range(start_pos, end_pos),
                py_reg_func=reg_func)
            results.append(decl)
            continue

        match1 = RE_PY_REGISTER_PACKED1.match(content)
        if match1:
            if line + 1 >= len(source):
                continue
            match_name = RE_PY_REGISTER_PACKED1_DEF.match(source[line + 1])
            if not match_name:
                continue
            start, end = match1.span()
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            reg_func = match1.group("reg")
            decl = PackedFuncDef(
                path=path, full_name=match_name.group("full_name"),
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


RE_PY_NAMESPACE_PREFIX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_.]+\Z")
RE_PY_VAR_NAME = re.compile(r"[a-zA-Z0-9_.]+")
RE_CC_GET_PACKED = re.compile(r"(GetPackedFunc|runtime::Registry::Get)\(\"\Z")

def extract_symbol(source, pos: Position):
    """Find the complete expression, include namespace prefix"""
    source = source.split("\n") if isinstance(source, str) else source
    content = source[pos.line]
    mprefix = RE_PY_NAMESPACE_PREFIX.search(content, 0, pos.character)
    start = mprefix.start() if mprefix else pos.character
    mvar = RE_PY_VAR_NAME.match(content, pos.character)
    end = mvar.end() if mvar else pos.character
    value = content[start:end]

    if end < len(content) and content[end] == "\"":
        if RE_CC_GET_PACKED.search(content, 0, start):
            return SymGetPackedFunc(value)
        return None
    return SymExpr(value)
