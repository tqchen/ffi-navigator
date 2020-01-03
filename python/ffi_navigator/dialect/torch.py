"""Torch FFI convention"""
import os
from .. import pattern

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
            pattern.Def(key="aten:"+match.group("key"), path=path, range=rg),
            use_search=True)
        self.py_ops = pattern.re_matcher(
            r"ops\.(?P<key_namespace>[a-z0-9|_|]+)\.(?P<key_op>[a-z0-9|_|]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key_namespace") + "::" + match.group("key_op"),
                        path=path, range=rg),
            use_search=True)
        self.py_variable_methods = pattern.re_matcher(
            r"torch\.([A-Za-z0-9|_]+\.)*(?P<key_op>[a-z0-9|_|]+)",
            lambda match, path, rg:
            pattern.Ref(key="aten:"+match.group("key_op"),
                        path=path, range=rg),
            use_search=True)

    def _cc_extract(self, path, source, begin, end):
        results = self.c10_reg(path, source, begin, end)
        generated_cpp = [
             os.path.join("generated", "python_nn_functions.cpp"),
             os.path.join("generated", "python_torch_functions.cpp"),
             os.path.join("generated", "python_variable_methods.cpp")
        ]
        for generated in generated_cpp:
            if path.endswith(generated):
                results += self.cpp_generated(path, source, begin, end)
        return results

    def _py_extract(self, path, source, begin, end):
        results = []
        results += self.py_ops(path, source, begin, end)
        results += self.py_variable_methods(path, source, begin, end)
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
