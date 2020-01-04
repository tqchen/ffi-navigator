import torch._C
import torch._jit_internal as _jit_internal
import torch.jit.annotations
import torch.testing
import torch.jit._recursive

from torch.jit._recursive import ScriptMethodStub
from torch.jit._builtins import _find_builtin, _get_builtin_table, _register_builtin  # noqa
from torch._jit_internal import _qualified_name
from torch.autograd import Variable, function
from torch.jit.frontend import get_jit_class_def, get_jit_def, get_default_args
from torch.nn import Module
from torch.serialization import validate_cuda_device
from torch._six import PY2, PY37, with_metaclass, string_classes, get_function_from_type
from torch.utils import set_module


_enabled = _parse_env('PYTORCH_JIT', True, "> Using PyTorch JIT", "> PyTorch JIT DISABLED")
_flatten = torch._C._jit_flatten
_unflatten = torch._C._jit_unflatten
_jit_script_class_compile = torch._C._jit_script_class_compile

# The Python CompilationUnit. All functions and modules defined in Python will
# live in here. It's defined in Python because doing in cpp creates static
# destruction order issues.
_python_cu = torch._C.CompilationUnit()

Future = torch._C.Future
set_module(Future, "torch.jit")
_fork = torch._C.fork
_wait = torch._C.wait
