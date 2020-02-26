import sys
import torch
import types

class _QEngineProp(object):
    def __get__(self, obj, objtype):
        return _get_qengine_str(torch._C._get_qengine())

    def __set__(self, obj, val):
        torch._C._set_qengine(_get_qengine_id(val))

class _SupportedQEnginesProp(object):
    def __get__(self, obj, objtype):
        qengines = torch._C._supported_qengines()
        return [_get_qengine_str(qe) for qe in qengines]

    def __set__(self, obj, val):
        raise RuntimeError("Assignment not supported")
