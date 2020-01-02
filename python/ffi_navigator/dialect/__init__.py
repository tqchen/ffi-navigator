"""Namespace for FFI export dialects"""
import os
from .tvm import TVMProvider
from .mxnet import MXNetProvider


class NoOpProvider:
    """A provider for projects without a registered dialect.
    """
    def __init__(self, resolver, logger):
        self.resolver = resolver
        self.logger = logger

    def _cc_extract(self, path, source, begin, end):
        return []

    def _py_extract(self, path, source, begin, end):
        return []

    def init_pass(self, path, source):
        pass

    def extract(self, path, source, begin=0, end=None):
        return []

    def extract_symbol(self, path, source, pos):
        return None


def create_dialect(root_path, resolver, logger):
    if os.path.exists(os.path.join(root_path, "python", "tvm")):
        return TVMProvider(resolver, logger)
    elif os.path.exists(os.path.join(root_path, "python", "mxnet")):
        return MXNetProvider(resolver, logger)
    else:
        return NoOpProvider(resolver, logger)
