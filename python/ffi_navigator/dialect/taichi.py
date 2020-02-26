"""Taichi FFI convention"""
import os
from .. import pattern
from .base_provider import BaseProvider


class TaichiProvider(BaseProvider):
    """Provider for Taichi FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        super().__init__(resolver, logger, "taichi")
        self.cpp_pybind_func = pattern.re_match_pybind_method()
        self.cpp_pybind_class = pattern.re_match_pybind_class()
        # ti.core.global_var_expr_from_snode
        # taichi_lang_core.expr_add, taichi_lang_core.create_kernel
        # tc_core.Array2DVector4
        self.py_ti_core = pattern.re_matcher(r"[\.|_]?core\.(?P<key>[A-Za-z0-9_]+)",
                                             lambda match, path, rg:
                                             pattern.Ref(key=match.group("key"), path=path, range=rg),
                                             use_search=True)

    def get_additional_scan_dirs(self, root_path):
        return [os.path.join(root_path, "taichi")]

    def _cc_extract(self, path, source, begin, end):
        results = self.cpp_pybind_func(path, source)
        results += self.cpp_pybind_class(path, source)
        return results

    def _py_extract(self, path, source, begin, end):
        return self.py_ti_core(path, source, begin, end)
