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


@attr.s
class PyImport:
    """Python import"""
    from_mod : Optional[str] = attr.ib()
    import_name : str = attr.ib()
    alias : Optional[str] = attr.ib()


# Register packed function in c++
RE_CC_REGISTER_PACKED = re.compile(r"\s*(TVM_REGISTER_GLOBAL|TVM_REGISTER_API)\(\"(?P<full_name>[^\"]+)\"\)")

RE_PY_IMPORT = re.compile(r"\s*from\s+(?P<mod>[^\s]+)\s+import\s+(?P<name>[^\s]+)" +
                          r"(\s+as\s+(?P<alias>[^\s]+))?")

RE_PY_INIT_API = re.compile(r"_init_api\(\"(?P<api_name>[^\"]+)\"")

RE_PY_NAMESPACE_PREFIX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_.]+\Z")
RE_PY_VAR_NAME = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]+")


def find_pyimports(source):
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_PY_IMPORT.match(content)
        if match:
            results.append(PyImport(from_mod=match.group("mod"),
                                    import_name=match.group("name"),
                                    alias=match.group("alias")))
    return results


def find_register_packed_macro(path, source, macro_suffix, packed_prefix):
    rexpr = re.compile(r"\s*REGISTER_" + macro_suffix + r"[^\(]*\((?P<name>[^\),]+)")
    # Special handling of api registery
    # consider not use the macro later
    results = []
    for line, content in enumerate(source):
        match = rexpr.match(content)
        if match:
            start, end = match.span("name")
            start_pos = Position(line, start)
            end_pos = Position(line, end)
            decl = PackedFuncDef(
                path=path, full_name=packed_prefix+match.group("name"),
                range=Range(start_pos, end_pos))
            results.append(decl)
    return results


def find_register_packed(path, source):
    """Find packed function registry pattern."""
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


def find_init_api(source):
    """Find _init_api."""
    source = source.split("\n") if isinstance(source, str) else source
    results = []
    for line, content in enumerate(source):
        match = RE_PY_INIT_API.match(content)
        if match:
            results.append(match.group("api_name"))
    return results

def extract_expr(source, pos: Position):
    """Find the complete expression, include namespace prefix"""
    source = source.split("\n") if isinstance(source, str) else source
    content = source[pos.line]
    mprefix = RE_PY_NAMESPACE_PREFIX.search(content, 0, pos.character)
    start = mprefix.start() if mprefix else pos.character
    mvar = RE_PY_VAR_NAME.match(content, pos.character)
    end = mvar.end() if mvar else pos.character
    return content[start:end]
