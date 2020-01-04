"""Torch FFI convention"""
import os
import re
from .. import pattern
from ..lsp import Range, Position
from .base_provider import BaseProvider


class TorchProvider(BaseProvider):
    """Provider for Torch FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        super().__init__(resolver, logger, "torch")
        # A pattern for c10 regesterd operators
        # c10::RegisterOperators()
        #   .op("quantized::conv2d",
        #       c10::RegisterOperators::options().kernel<QConvInt8<2, false>>(
        #       TensorTypeId::QuantizedCPUTensorId))
        self.c10_reg = pattern.re_matcher(
            r"\.op\(\s*\"(?P<key>[a-z0-9|_|::]+)(.*)\"",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)
        # A pattern for generated methods under torch/csrc/autograd/generated
        # You need to have built PyTorch from source for this pattern to work
        # {"conv1d", (PyCFunction)(void(*)(void))THPVariable_conv1d, ...
        # {"conv2d", (PyCFunction)(void(*)(void))THPVariable_conv2d, ...
        # {"conv3d", (PyCFunction)(void(*)(void))THPVariable_conv3d, ...
        self.cpp_generated = pattern.re_matcher(
            r"{\"(?P<key>[a-z0-9|_]+)\"",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)
        # A pattern for pybind-wrapped functions
        # .def(
        #     "_jit_pass_insert_prepack_unpack",
        #     [](std::shared_ptr<Graph>& g) { return InsertPrepackUnpack(g); })
        self.cpp_pybind_func = \
          pattern.re_multi_line_matcher(r"\.def\(\s*\"(?P<key>[a-z0-9|_]+)\"",
                                        lambda match, path, rg: \
                                        pattern.Def(key=match.group("key"), path=path, range=rg))
        # A pattern for pybind-wrapped classes
        # py::class_<Method>(m, "ScriptMethod", py::dynamic_attr())
        # py::class_<CompilationUnit, std::shared_ptr<CompilationUnit>>(
        #     m, "CompilationUnit")
        self.cpp_pybind_class = \
          pattern.re_multi_line_matcher(r"py::class_\<[A-Za-z0-9|_|::|<|>]+(\,\s*[A-Za-z0-9|_|::|<|>]+)*\>"
                                        r"\s*\(\s*m,\s*\"(?P<key>[A-Za-z0-9|_]+)\""
                                        r"(,\s*[A-Za-z0-9|_|::|<|>|(|)]+)*\)",
                                        lambda match, path, rg: \
                                        pattern.Def(key=match.group("key"), path=path, range=rg))
        # torch.ops.quantized.conv2d_relu (c10 ops)
        self.py_ops = pattern.re_matcher(
            r"ops\.(?P<key_namespace>[a-z0-9|_|]+)\.(?P<key_op>[a-z0-9|_|]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key_namespace") + "::" + match.group("key_op"),
                        path=path, range=rg),
            use_search=True)
        # torch.conv1d, torch._C._nn.avg_pool2d (variable methods)
        # torch._C._jit_script_class_compile (for jit etc)
        # torch._C.ScriptMethod, torch._C.CompilationUnit
        self.py_wrapped = pattern.re_matcher(
            r"torch\.([A-Za-z0-9|_]+\.)*(?P<key>[A-Za-z0-9|_|]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key"),
                        path=path, range=rg),
            use_search=True)

    def get_additional_scan_dirs(self, root_path):
        return [
            os.path.join(root_path, "aten", "src", "ATen"),
            os.path.join(root_path, "torch")
        ]

    def _cc_extract(self, path, source, begin, end):
        results = self.c10_reg(path, source, begin, end)
        results += self.cpp_pybind_func(path, source)
        results += self.cpp_pybind_class(path, source)
        generated_cpp = [
             os.path.join("generated", "python_nn_functions.cpp"),
             os.path.join("generated", "python_torch_functions.cpp"),
             os.path.join("generated", "python_variable_methods.cpp")
        ]
        for generated in generated_cpp:
            if path.endswith(generated):
                results += self.cpp_generated(path, source, begin, end)
        return results

    def _py_extract(self, path, source, begin, end):
        results = []
        results += self.py_ops(path, source, begin, end)
        results += self.py_wrapped(path, source, begin, end)
        return results

    def extract(self, path, source, begin=0, end=None):
        if not path.endswith("_test.cpp"):
            return super().extract(path, source, begin, end)
        return []
