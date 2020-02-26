"""FFI related code patterns and utility function to detect them."""
from typing import Optional

import re
import attr
import numpy as np
from bisect import bisect

from .lsp import Range, Position, Location


class Pattern:
    """Base class of all interesting code patterns."""
    pass


@attr.s
class Def(Pattern):
    """Definition of an FFI resource.

    Parameters
    ----------
    key : str
        Global unique id to locate the FFI resource.

    path : str
        The file path.

    range: Range
        The location range of the defininition.
    """
    key : str = attr.ib()
    path : str = attr.ib()
    range: Range = attr.ib()


@attr.s
class Ref(Pattern):
    """Reference of an FFI resource.

    Parameters
    ----------
    key : str
        Global unique id to locate the FFI resource.

    path : str
        The file path.

    range: Range
        The location range of the defininition.
    """
    key : str = attr.ib()
    path : str = attr.ib()
    range : Range = attr.ib()


@attr.s
class Export(Pattern):
    """Export a collection of keys with the same prefix.

    Parameters
    ----------
    key_prefix : str
        The prefix of keys to be exported.

    path : str
        The file path to be exported.

    fkey2var : Function
        The function that takes a key and maps to a local var
        in the path which corresponds to the FFI resource.

    fvar2key : Function
        The function that takes local var name and maps
        to the corresponding key, can return None.
    """
    key_prefix : str = attr.ib()
    path : str = attr.ib()
    fkey2var = attr.ib()
    fvar2key = attr.ib()

@attr.s
class Symbol(Pattern):
    """A symbol in python expression, can contain dot.
    """
    value : str = attr.ib()


def re_matcher(rexpr, fcreate, use_search=False):
    """
    Parameters
    ----------
    rexpr : str
        A regexp pattern to match.

    fcreate : Function (match, path, range) -> result.

    use_search: bool
         Whether use search
    """
    rexpr = re.compile(rexpr)

    def _matcher(path, source, begin_line=0, end_line=None):
        source = source.split("\n") if isinstance(source, str) else source
        results = []
        end_line = min(end_line, len(source)) if end_line else len(source)
        for line in range(begin_line, end_line):
            content = source[line]
            match = rexpr.search(content) if use_search else rexpr.match(content)
            if match:
                start, end = match.span()
                start_pos = Position(line, start)
                end_pos = Position(line, end)
                item = fcreate(match, path,
                               Range(start_pos, end_pos))
                if item:
                    results.append(item)
        return results
    return _matcher


def re_multi_line_matcher(rexpr, fcreate):
    """ Matches a pattern spanning multiple lines

    Parameters
    ----------
    rexpr : str
        A regexp pattern to match.

    fcreate : Function (match, path, range) -> result.
    """
    rexpr = re.compile(rexpr)

    def _matcher(path, lines):
        source = "".join(lines)
        matches = list(rexpr.finditer(source))
        if matches == []:
            return []
        line_counts = map(lambda line: len(line), lines)
        cumsum = np.cumsum(list(line_counts))

        # find line num, start and end pos for each match
        next_begin = 0
        result = []
        for match in matches:
            line_num_start = bisect(cumsum[next_begin:], match.start()) + next_begin
            next_begin = line_num_start
            line_num_end = line_num_start + match.group().count("\n")
            pos_start = match.start() - int(cumsum[line_num_start-1])
            pos_end = match.end() - int(cumsum[line_num_end-1])
            assert(pos_start >= 0 and pos_end >= 0)
            rg = Range(Position(line_num_start, pos_start), Position(line_num_end, pos_end))
            result.append(fcreate(match, path, rg))

        return result
    return _matcher


def re_match_pybind_class():
    return re_multi_line_matcher(r"py::class_\<[A-Za-z0-9|_|::|<|>]+(\,\s*[A-Za-z0-9|_|::|<|>]+)*\>"
                                 r"\s*\(\s*m,\s*\"(?P<key>[A-Za-z0-9|_]+)\""
                                 r"(,\s*[A-Za-z0-9|_|::|<|>|(|)]+)*\)",
                                 lambda match, path, rg: \
                                 Def(key=match.group("key"), path=path, range=rg))


def re_match_pybind_method():
    return re_multi_line_matcher(r"\.def\(\s*\"(?P<key>[a-z0-9|_]+)\"",
                                 lambda match, path, rg: \
                                 Def(key=match.group("key"), path=path, range=rg))


def macro_matcher(macro_names, fcreate=None):
    """Match pattern <macro_name>("<skey>"

    Parameters
    ----------
    macro_names : list
        List of macro names to match.

    fcreate : Function (skey, path, range, macro_name) -> result.
    """
    rexpr = r"(?P<macro_name>("
    rexpr += "|".join(re.escape(x)  for x in macro_names)
    rexpr += r"))\(\"(?P<skey>[^\"]+)\"\)?"
    def _fcreate(match, path, rg):
        return fcreate(match.group("skey"), path,
                       rg,
                       match.group("macro_name"))
    return re_matcher(rexpr, _fcreate)


def func_get_searcher(func_names, fcreate=None):
    """Search pattern <func_name>("<skey>")

    Parameters
    ----------
    func_names : list
        List of macro names to match.

    fcreate : Function (skey, path, range, func_name) -> result.
    """
    rexpr = r"(?P<func_name>("
    rexpr += "|".join(re.escape(x)  for x in func_names)
    rexpr += r"))\(\"(?P<skey>[^\"]+)\"\)"
    rexpr = re.compile(rexpr)

    def _matcher(path, source, begin_line=0, end_line=None):
        source = source.split("\n") if isinstance(source, str) else source
        results = []
        end_line = min(end_line, len(source)) if end_line else len(source)
        for line in range(begin_line, end_line):
            content = source[line]
            str_pos = 0
            while True:
                match = rexpr.search(content, str_pos)
                if not match:
                    break
                start, end = match.span("skey")
                start_pos = Position(line, start)
                end_pos = Position(line, end)
                item = fcreate(match.group("skey"), path,
                               Range(start_pos, end_pos),
                               match.group("func_name"))
                if item:
                    results.append(item)
                str_pos = match.end()
        return results
    return _matcher


def decorator_matcher(func_names, keyword, fcreate=None):
    """Search pattern @[namespace]<func_name>("<skey>")

    Parameters
    ----------
    func_names : list
        List of macro names to match.

    fcreate : Function (skey, path, range, func_name) -> result.
    """

    decorator = r"@?(?P<decorator>([a-zA-Z_]?[a-zA-Z_0-9.]*.)?("
    decorator += "|".join(re.escape(x)  for x in func_names)
    decorator += "))((\(\"(?P<skey>[^\"]+)\")|(\s*\Z))"
    nextline = keyword + r"\s+(?P<skey>[a-zA-Z_0-9]+)\("

    decorator = re.compile(decorator)
    nextline = re.compile(nextline)

    def _matcher(path, source, begin_line=0, end_line=None):
        source = source.split("\n") if isinstance(source, str) else source
        results = []
        end_line = min(end_line, len(source)) if end_line else len(source)
        for line in range(begin_line, end_line):
            content = source[line]
            match = decorator.match(content)

            if match:
                skey = match.group("skey")
                if skey:
                    start, end = match.span("skey")
                    lineno = line
                if not skey and line + 1 < len(source):
                    match_name = nextline.match(source[line + 1])
                    if match_name:
                        skey = match_name.group("skey")
                        start, end = match_name.span("skey")
                        lineno = line + 1
                if skey:
                    start_pos = Position(lineno, start)
                    end_pos = Position(lineno, end)
                    item = fcreate(skey, path,
                                Range(start_pos, end_pos),
                                   match.group("decorator"))
                    if item:
                        results.append(item)
        return results
    return _matcher


@attr.s
class PyImport:
    """Python import syntax."""
    from_mod : Optional[str] = attr.ib()
    import_name : str = attr.ib()
    alias : Optional[str] = attr.ib()

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


RE_PY_DELIM = r"(\s|[.,\(\)\[\]{}:=\+\-\*]|\Z)+"

def search_symbol(source,  symbols):
    """Search symbols within a source, return matched positions."""
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


RE_PY_NAMESPACE_PREFIX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_.]+\Z")
RE_PY_VAR_NAME = re.compile(r"[a-zA-Z0-9_.]+")

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
        return None
    return Symbol(value)
