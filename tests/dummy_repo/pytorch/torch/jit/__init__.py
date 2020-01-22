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


def trace_module(mod,
                 inputs,
                 optimize=None,
                 check_trace=True,
                 check_inputs=None,
                 check_tolerance=1e-5,
                 _force_outplace=False,
                 _module_class=None,
                 _compilation_unit=_python_cu):
    if not _enabled:
        return mod
    if optimize is not None:
        warnings.warn("`optimize` is deprecated and has no effect. Use `with torch.jit.optimized_execution() instead")

    var_lookup_fn = _create_interpreter_name_lookup_fn(0)

    if not isinstance(mod, torch.nn.Module):
        raise AttributeError("expected torch.nn.Module as the first argument")

    if not isinstance(inputs, dict):
        raise AttributeError("expected a dictionary of (method_name, input) pairs")

    old_module_map = torch.jit._trace_module_map
    try:
        torch.jit._trace_module_map = {}

        def register_submods(mod, prefix):
            for name, child in mod.named_children():
                submod_qualname = prefix + '.' + name
                torch.jit._trace_module_map[child] = submod_qualname
                register_submods(child, submod_qualname)

        torch.jit._trace_module_map['__module'] = mod
        register_submods(mod, '__module')

        module = make_module(mod, _module_class, _compilation_unit)

        for method_name, example_inputs in inputs.items():
            # this is needed since Module.__call__ sets up some extra tracing
            func = mod if method_name == "forward" else getattr(mod, method_name)
            example_inputs = make_tuple(example_inputs)
            module._c._create_method_from_trace(method_name, func, example_inputs, var_lookup_fn, _force_outplace)
            check_trace_method = module._c._get_method(method_name)

            # Check the trace against new traces created from user-specified inputs
            if check_trace:
                if check_inputs is not None:
                    _check_trace(check_inputs, func, check_trace_method,
                                 check_tolerance, _force_outplace, True, _module_class)
                else:
                    _check_trace([inputs], func, check_trace_method,
                                 check_tolerance, _force_outplace, True, _module_class)
    finally:
        torch.jit._trace_module_map = old_module_map

    return module
