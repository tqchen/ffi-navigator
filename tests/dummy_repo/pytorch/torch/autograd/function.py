import torch
import torch._C as _C


class Function(with_metaclass(FunctionMeta, _C._FunctionBase, _ContextMethodMixin, _HookMixin)):
    __call__ = _C._FunctionBase._do_forward
