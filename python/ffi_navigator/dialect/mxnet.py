"""MXNet FFI convention"""
import os
from .. import pattern
from .base_provider import BaseProvider


class MXNetProvider(BaseProvider):
    """Provider for MXNet FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        super().__init__(resolver, logger, "mxnet")
        self.cc_c_api = pattern.re_matcher(
            r"\s*int\s*(?P<key>MX[A-Za-z0-9]+)",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg))
        self.py_lib = pattern.re_matcher(
            r".*_LIB\.(?P<key>MX[A-Za-z0-9]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key"), path=path, range=rg))

    def _cc_extract(self, path, source, begin, end):
        if "c_api" in path:
            return self.cc_c_api(path, source, begin, end)
        return []

    def _py_extract(self, path, source, begin, end):
        return self.py_lib(path, source, begin, end)
