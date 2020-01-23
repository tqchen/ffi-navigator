import torch
import warnings

from .variable import Variable
from .function import Function, NestedIOFunction
from .gradcheck import gradcheck, gradgradcheck
from .grad_mode import no_grad, enable_grad, set_grad_enabled
from .anomaly_mode import detect_anomaly, set_detect_anomaly
from . import profiler


def backward(tensors, grad_tensors=None, retain_graph=None, create_graph=False, grad_variables=None):
    tensors = (tensors,) if isinstance(tensors, torch.Tensor) else tuple(tensors)
    if grad_tensors is None:
        grad_tensors = [None] * len(tensors)
    elif isinstance(grad_tensors, torch.Tensor):
        grad_tensors = [grad_tensors]
    else:
        grad_tensors = list(grad_tensors)

    grad_tensors = _make_grads(tensors, grad_tensors)
    if retain_graph is None:
        retain_graph = create_graph

    Variable._execution_engine.run_backward(
        tensors, grad_tensors, retain_graph, create_graph,
        allow_unreachable=True)  # allow_unreachable flag
