"""Class for NodeFlow data structure."""
from __future__ import absolute_import

from ._ffi.object import register_object, ObjectBase
from ._ffi.function import _init_api
from .base import ALL, is_all, DGLError
from . import backend as F
from .frame import Frame, FrameRef
from .graph import DGLBaseGraph
from .graph_index import transform_ids
from .runtime import ir, scheduler, Runtime
from . import utils
from .view import LayerView, BlockView

__all__ = ['NodeFlow']

@register_object('graph.NodeFlow')
class NodeFlowObject(ObjectBase):
    """NodeFlow object"""

    @property
    def graph(self):
        """The graph structure of this nodeflow.

        Returns
        -------
        GraphIndex
        """
        return _CAPI_NodeFlowGetGraph(self)
