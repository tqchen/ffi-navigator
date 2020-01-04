r"""Functional interface"""
from __future__ import division

import warnings
import math

import torch
from torch._C import _infer_size, _add_docstr
from . import _reduction as _Reduction
from .modules import utils
from .modules.utils import _single, _pair, _triple, _list_with_default
from . import grad  # noqa: F401
from . import _VF
from .._jit_internal import boolean_dispatch, List


conv2d = _add_docstr(torch.conv2d, r"")
