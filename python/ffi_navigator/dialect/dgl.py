"""DGL FFI convention"""
import os
from .. import pattern

class DGLProvider:
    """Provider for DGL FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        self.resolver = resolver
        self.cc_def_packed = pattern.macro_matcher(
            ["DGL_REGISTER_API", "DGL_REGISTER_GLOBAL"],
            lambda key, path, rg, _:
            pattern.Def(key=key, path=path, range=rg))
        self.cc_def_object = pattern.re_matcher(
            r"\s*static\s+constexpr\sconst\s+char\s*\*\s+_type_key\s*=\s*\"(?P<key>[^\"]+)\"",
            lambda match, path, rg:
            pattern.Def(key="t:"+match.group("key"), path=path, range=rg),
            use_search=True)
        self.cc_get_packed = pattern.func_get_searcher(
            ["GetPackedFunc", "runtime::Registry::Get"],
            lambda key, path, rg, _:
            pattern.Ref(key=key, path=path, range=rg))
        self.py_init_api = pattern.macro_matcher(
            ["_init_api"], lambda key, path, *_: self._wrap_py_init_api(key, path))
        self.py_reg_object = pattern.decorator_matcher(
            ["register_object"], "class",
            lambda key, path, rg, reg:
            pattern.Ref(key="t:"+key, path=path, range=rg))
        self.py_reg_func = pattern.decorator_matcher(
            ["register_func"], "def",
            lambda key, path, rg, reg: self._wrap_py_reg_func(key, path, rg, reg))

        self._pypath_api_internal = None
        self._pypath_funcmod = None
        self._pypath_root = None
        self._pypath_init = None
        self.logger = logger

    def _wrap_py_reg_func(self, key, path, rg, reg):
        new_mod, new_name = self.resolver.resolve(path, reg)
        if (new_mod not in (self._pypath_funcmod, self._pypath_init)
            or new_name != "register_func"):
            return None
        return pattern.Def(key=key, path=path, range=rg)

    def _wrap_py_init_api(self, key, path):
        new_mod, new_name = self.resolver.resolve(path, "_init_api")
        if new_mod != self._pypath_funcmod or new_name != "_init_api":
            return None
        prefix = key[4:] if key.startswith("dgl.") else key
        fkey2var = lambda k : k[len(prefix) + 1:]
        fvar2key = lambda v : prefix + "." + v

        return pattern.Export(key_prefix=prefix, path=path,
                              fvar2key=fvar2key,
                              fkey2var=fkey2var)

    def _cc_extract(self, path, source, begin, end):
        results = []
        results += self.cc_def_packed(path, source, begin, end)
        results += self.cc_def_object(path, source)
        results += self.cc_get_packed(path, source)
        return results

    def _py_extract(self, path, source, begin, end):
        results = []
        results += self.py_init_api(path, source, begin, end)
        results += self.py_reg_object(path, source, begin, end)
        results += self.py_reg_func(path, source, begin, end)
        if path.startswith(self._pypath_api_internal):
            export_item = pattern.Export(
                key_prefix="_", path=path,
                fvar2key=lambda x: x,
                fkey2var=lambda x: x)
            results.append(export_item)
        return results

    def init_pass(self, path, source):
        """This function will be called for each file before extract."""
        if path.endswith("python/dgl/__init__.py"):
            self._pypath_root = os.path.abspath(path[:-len("/__init__.py")])
            self._pypath_init = os.path.abspath(path[:-len(".py")])
            self._pypath_funcmod = os.path.join(self._pypath_root, "_ffi", "function")
            self._pypath_api_internal = os.path.join(self._pypath_root, "_api_internal")
            self.resolver.add_package("dgl", self._pypath_root)
            self.logger.info("DGL: find python path %s", self._pypath_root)

    def extract(self, path, source, begin=0, end=None):
        """This function will be called for each file

        Extract patterns in the file as specified in pattern.py and return them.
        """
        if path.endswith(".cc") or path.endswith(".h"):
            return self._cc_extract(path, source, begin, end)
        elif path.endswith(".py"):
            return self._py_extract(path, source, begin, end)
        return []

    def extract_symbol(self, path, source, pos):
        """Extract possible pattern in the specified location, if not found, return None."""
        # only search a small context
        begin = max(pos.line - 1, 0)
        end = min(pos.line + 2, len(source))
        # We can use extract and verify to get the pattern.
        for res in self.extract(path, source, begin, end):
            if (isinstance(res, (pattern.Ref, pattern.Def)) and
                res.range.start.line <= pos.line and
                res.range.end.line >= pos.line and
                res.range.start.character <= pos.character and
                res.range.end.character >= pos.character):
                return res
        return None
