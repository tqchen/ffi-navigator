"""Namespace for FFI export dialects"""
import os
from .tvm import TVMProvider
from .mxnet import MXNetProvider


def create_dialect(root_path, resolver, logger):
    if os.path.exists(os.path.join(root_path, "python", "tvm")):
        return TVMProvider(resolver, logger)
    elif os.path.exists(os.path.join(root_path, "python", "mxnet")):
        return MXNetProvider(resolver, logger)
