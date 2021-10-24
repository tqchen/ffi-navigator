"""TVM FFI convention"""
import os
from .. import pattern
from ..util import normalize_path
from .base_provider import BaseProvider


class TVMProvider(BaseProvider):
    """Provider for TVM FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        super().__init__(resolver, logger, "tvm")
        self.cc_def_packed = pattern.macro_matcher(
            ["TVM_REGISTER_API", "TVM_REGISTER_GLOBAL"],
            lambda key, path, rg, _:
            pattern.Def(key=key, path=path, range=rg))
        self.cc_def_packed_ir = pattern.re_matcher(
            r"\s*(REGISTER_MAKE|REGISTER_MAKE_BINARY_OP)\((?P<key>[A-Za-z0-9]+)",
            lambda match, path, rg:
            pattern.Def(key="make."+match.group("key"), path=path, range=rg))
        self.cc_def_packed_pass = pattern.re_matcher(
            r"\s*REGISTER_PASS\((?P<key>[A-Za-z0-9]+)\)",
            lambda match, path, rg:
            pattern.Def(key="ir_pass."+match.group("key"), path=path, range=rg))
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
            ["tvm._ffi._init_api", "_init_api"],
            lambda key, path, _, reg: self._wrap_py_init_api(key, path, reg))
        self.py_reg_object = pattern.decorator_matcher(
            ["register_object", "register_node", "register_relay_node"], "class",
            lambda key, path, rg, reg:
            pattern.Ref(key="t:relay."+key, path=path, range=rg)
            if reg.endswith("relay_node")
            else pattern.Ref(key="t:"+key, path=path, range=rg))
        self.py_reg_func = pattern.decorator_matcher(
            ["register_func", "tvm._ffi.register_func"], "def",
            lambda key, path, rg, reg: self._wrap_py_reg_func(key, path, rg, reg))

        self._pypath_api_internal = None
        self._pypath_funcmod = None
        self._pypath_init = None

    def _wrap_py_reg_func(self, key, path, rg, reg):
        if reg != "tvm._ffi.register_func":
            new_mod, new_name = self.resolver.resolve(path, reg)
            if (new_mod not in (self._pypath_funcmod, self._pypath_init)
                or new_name != "register_func"):
                return None
        return pattern.Def(key=key, path=path, range=rg)

    def _wrap_py_init_api(self, key, path, reg):
        if reg != "tvm._ffi._init_api":
            # legacy behavior
            new_mod, new_name = self.resolver.resolve(path, "_init_api")
            if new_mod != self._pypath_funcmod or new_name != "_init_api":
                return None
        prefix = key[4:] if key.startswith("tvm.") else key
        fkey2var = lambda k : k[len(prefix) + 1:]
        fvar2key = lambda v : prefix + "." + v

        return pattern.Export(key_prefix=prefix, path=path,
                              fvar2key=fvar2key,
                              fkey2var=fkey2var)

    def _cc_extract(self, path, source, begin, end):
        results = []
        results += self.cc_def_packed(path, source, begin, end)
        if path.endswith("api_ir.cc"):
            results += self.cc_def_packed_ir(path, source, begin, end)
        if path.endswith("api_pass.cc"):
            results += self.cc_def_packed_pass(path, source, begin, end)
        results += self.cc_def_object(path, source)
        results += self.cc_get_packed(path, source)
        return results

    def _py_extract(self, path, source, begin, end):
        results = []
        results += self.py_init_api(path, source, begin, end)
        results += self.py_reg_object(path, source, begin, end)
        results += self.py_reg_func(path, source, begin, end)

        if self._pypath_api_internal and path.startswith(self._pypath_api_internal):
            export_item = pattern.Export(
                key_prefix="_", path=path,
                fvar2key=lambda x: x,
                fkey2var=lambda x: x)
            results.append(export_item)
        return results

    def init_pass(self, path, source):
        if path.endswith(normalize_path("python/tvm/__init__.py")):
            super().init_pass(path, source)
            self._pypath_init = os.path.abspath(path[:-len(".py")])
            self._pypath_funcmod = os.path.join(self._pypath_root, "_ffi", "function")
            self._pypath_api_internal = os.path.join(self._pypath_root, "_api_internal")
