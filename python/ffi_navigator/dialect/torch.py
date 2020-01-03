"""Torch FFI convention"""
import os
import re
import numpy as np
from bisect import bisect
from .. import pattern
from ..lsp import Range, Position


def _re_match_multi_line(pat, prefix, path, lines):
    source = "".join(lines)
    matches = list(re.finditer(r"\.def\((?P<key_space>\s*)\"(?P<key_func>[a-z0-9|_]+)\"", source))
    if matches == []:
        return []
    line_count = len(lines)
    cumsum = np.cumsum(list(map(lambda line: len(line)+1, lines))) # +1 for newline

    next_begin = 0
    result = []
    # find line num, start and end pos for each match
    for match in matches:
        line_num = bisect(cumsum[next_begin:], match.start()) + next_begin
        next_begin = line_num
        line_num_start = line_num
        line_num_end = line_num
        if match.group("key_space"):
            line_num_end += 1
        pos_start = match.start() - cumsum[line_num_start-1]
        pos_end = match.end() - cumsum[line_num_end-1]
        rg = Range(Position(line_num_start, pos_start), Position(line_num_end, pos_end))
        key = prefix + match.group("key_func")
        result.append(pattern.Def(key=key, path=path, range=rg))

    return result


class TorchProvider:
    """Provider for Torch FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        self.resolver = resolver
        self._pypath_root = None
        self.logger = logger
        self.c10_reg = pattern.re_matcher(
            r"\.op\(\s*\"(?P<key>[a-z0-9|_|::]+)(.*)\"",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)
        self.cpp_generated = pattern.re_matcher(
            r"{\"(?P<key>[a-z0-9|_|::]+)\"",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)
        self.cpp_pybind_func = lambda path, lines: \
          _re_match_multi_line(r"\.def\(\s*\"(?P<key_func>[a-z0-9|_]+)\"", "", path, lines)
        self.py_ops = pattern.re_matcher(
            r"ops\.(?P<key_namespace>[a-z0-9|_|]+)\.(?P<key_op>[a-z0-9|_|]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key_namespace") + "::" + match.group("key_op"),
                        path=path, range=rg),
            use_search=True)
        self.py_variable_methods = pattern.re_matcher(
            r"torch\.([A-Za-z0-9|_]+\.)*(?P<key_op>[a-z0-9|_|]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key_op"),
                        path=path, range=rg),
            use_search=True)
                    # torch._C._jit_pass_inline(mod_canonicalized)
        self.py_pybind_func = pattern.re_matcher(
            r"torch\._C\.(?P<key_func>[a-z0-9|_]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key_func"),
                        path=path, range=rg),
            use_search=True)

    def _cc_extract(self, path, source, begin, end):
        results = self.c10_reg(path, source, begin, end)
        results += self.cpp_pybind_func(path, source)
        generated_cpp = [
             os.path.join("generated", "python_nn_functions.cpp"),
             os.path.join("generated", "python_torch_functions.cpp"),
             os.path.join("generated", "python_variable_methods.cpp")
        ]
        for generated in generated_cpp:
            if path.endswith(generated):
                results += self.cpp_generated(path, source, begin, end)
        for res in results:
            self.logger.info("Extracted %s from %s", res.key, res.path)
        return results

    def _py_extract(self, path, source, begin, end):
        results = []
        results += self.py_ops(path, source, begin, end)
        results += self.py_variable_methods(path, source, begin, end)
        results += self.py_pybind_func(path, source, begin, end)
        for res in results:
            self.logger.info("Py: Extracted %s from %s", res.key, res.path)

        return results

    def init_pass(self, path, source):
        """This function will be called for each file before extract."""
        if path.endswith("torch/__init__.py"):
            self._pypath_root = os.path.abspath(path[:-len("/__init__.py")])
            self.resolver.add_package("torch", self._pypath_root)
            self.logger.info("Torch: find python path %s", self._pypath_root)

    def extract(self, path, source, begin=0, end=None):
        """This function will be called for each file
        Extract patterns in the file as specified in pattern.py and return them.
        """
        if path.endswith(".cpp") and not path.endswith("_test.cpp"):
            self.logger.info("Extracting from %s", path)
            return self._cc_extract(path, source, begin, end)
        return []

    def extract_symbol(self, path, source, pos):
        """Extract possible pattern in the specified location, if not found, return None."""
        # only search a small context
        begin = max(pos.line - 1, 0)
        end = min(pos.line + 2, len(source))
        # We can use extract and verify to get the pattern.
        if path.endswith(".py"):
            for res in self._py_extract(path, source, begin, end):
                if (isinstance(res, (pattern.Ref, pattern.Def)) and
                    res.range.start.line <= pos.line and
                    res.range.end.line >= pos.line and
                    res.range.start.character <= pos.character and
                    res.range.end.character >= pos.character):
                    return res
        return None

    def get_additional_scan_dirs(self, root_path):
        return [
            os.path.join(root_path, "aten", "src", "ATen"),
            os.path.join(root_path, "torch")
        ]
