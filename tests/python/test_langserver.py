from ffi_navigator import langserver
from ffi_navigator.util import join_path, normalize_path

import logging
import os

curr_path = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))

def run_find_definition(server, path, line, character):
    uri = langserver.path2uri(path)
    res = server.m_text_document__definition(
        textDocument={"uri": uri},
        position={"line": line, "character": character })
    return res


def run_find_references(server, path, line, character):
    uri = langserver.path2uri(path)
    res = server.m_text_document__references(
        textDocument={"uri": uri},
        position={"line": line, "character": character })
    return res


def test_tvm_dialect():
    def test_dummy_repo():
        # test and verify against dummy repo
        tvm_path = os.path.join(curr_path, "..",  "dummy_repo", "tvm")
        server = langserver.BaseServer()
        server.m_initialize(rootUri=langserver.path2uri(tvm_path))

        # Constant
        res = run_find_definition(server,
                                  join_path(tvm_path, "python/tvm/relay/expr.py"),
                                  15, 14)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("expr.h"))
        assert(res[0]['range']['start']['line'] == 33)

        # _make.ProducerConsumer
        res = run_find_definition(server,
                                  join_path(tvm_path, "python/tvm/stmt.py"),
                                  26, 30)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("api_ir.cc"))
        assert(res[0]['range']['start']['line'] == 14)

        # _make.LetStmt
        res = run_find_definition(server,
                                  join_path(tvm_path, "python/tvm/stmt.py"),
                                  46, 20)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("api_ir.cc"))
        assert(res[0]['range']['start']['line'] == 15)

        # Get("relay.backend.lower") from c++ to python
        res = run_find_definition(server,
                                  join_path(tvm_path, "src/relay/backend/compile_engine.cc"),
                                  74, 59)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("_backend.py"))
        assert(res[0]['range']['start']['line'] == 8)

        # Variable
        res = run_find_references(server,
                                  join_path(tvm_path, "include/tvm/expr.h"),
                                  15, 49)
        assert(len(res) == 2)
        assert(res[1]['uri'].endswith("expr.py"))
        assert(res[1]['range']['start']['line'] == 15)

        # TVM_REGISTER_GLOBAL("_min_value")
        res = run_find_references(server,
                                  join_path(tvm_path, "src/api/api_lang.cc"),
                                  15, 33)
        assert(len(res) == 2)
        assert(res[1]['uri'].endswith("api.py"))
        assert(res[1]['range']['start']['line'] == 24)

        # _make.Constant
        res = run_find_references(server,
                                  join_path(tvm_path, "src/relay/ir/expr.cc"),
                                  16, 33)
        assert(len(res) == 2)
        assert(res[1]['uri'].endswith("expr.py"))
        assert(res[1]['range']['start']['line'] == 24)

        # REGISTER_MAKE(ProducerConsumer)
        res = run_find_references(server,
                                  join_path(tvm_path, "src/api/api_ir.cc"),
                                  14, 25)
        assert(len(res) == 3)
        assert(res[1]['uri'].endswith("stmt.py"))
        assert(res[1]['range']['start']['line'] == 26)

        # REGISTER_MAKE(LetStmt)
        res = run_find_references(server,
                                  join_path(tvm_path, "src/api/api_ir.cc"),
                                  15, 18)
        assert(len(res) == 2)
        assert(res[1]['uri'].endswith("stmt.py"))
        assert(res[1]['range']['start']['line'] == 46)

        # @register_func("relay.backend.build")
        res = run_find_references(server,
                                  join_path(tvm_path, "python/tvm/relay/backend/_backend.py"),
                            26, 30)
        assert(len(res) == 3)
        assert(res[1]['uri'].endswith("compile_engine.cc"))
        assert(res[1]['range']['start']['line'] == 90)
        assert(res[2]['uri'].endswith("interpreter.cc"))
        assert(res[2]['range']['start']['line'] == 115)

        # _pass.Simplify(end - begin)
        res = run_find_references(server,
                                  join_path(tvm_path, "python/tvm/ir_builder.py"),
                                  20, 48)
        assert(len(res) == 6)
        assert(res[0]['uri'].endswith("api_pass.cc"))
        assert(res[0]['range']['start']['line'] == 10)
        assert(res[1]['uri'].endswith(normalize_path("autotvm/util.py")))
        assert(res[1]['range']['start']['line'] == 26)
        assert(res[2]['uri'].endswith(normalize_path("autotvm/util.py")))
        assert(res[2]['range']['start']['line'] == 50)
        assert(res[3]['uri'].endswith("build_module.py"))
        assert(res[3]['range']['start']['line'] == 98)
        assert(res[4]['uri'].endswith(normalize_path("hybrid/parser.py")))
        assert(res[4]['range']['start']['line'] == 43)

        # REGISTER_MAKE(Provide);
        res = run_find_references(server,
                                  join_path(tvm_path, "src/api/api_ir.cc"),
                                  16, 15)
        assert(len(res) == 6)
        assert(res[1]['uri'].endswith(normalize_path("hybrid/parser.py")))
        assert(res[1]['range']['start']['line'] == 75)
        assert(res[2]['uri'].endswith(normalize_path("hybrid/parser.py")))
        assert(res[2]['range']['start']['line'] == 81)
        assert(res[3]['uri'].endswith(normalize_path("hybrid/parser.py")))
        assert(res[3]['range']['start']['line'] == 97)
        assert(res[4]['uri'].endswith(normalize_path("hybrid/util.py")))
        assert(res[4]['range']['start']['line'] == 20)
        assert(res[5]['uri'].endswith("stmt.py"))
        assert(res[5]['range']['start']['line'] == 68)

    def test_real_repo():
        # tested on tvm git tag e69bd1284b50630df570b3a5779a801982203756
        tvm_path = os.path.join(curr_path, "..", "..", "..", "tvm")
        if not os.path.exists(tvm_path):
            logging.info("Skip tvm tests")
            return

        server = langserver.BaseServer()
        server.m_initialize(rootUri=langserver.path2uri(tvm_path))

        run_find_references(server,
                            join_path(tvm_path, "src/runtime/module.cc"),
                            198, 34)

        run_find_references(server,
                            join_path(tvm_path, "python/tvm/api.py"),
                            58, 33)

        run_find_definition(server,
                            join_path(tvm_path, "python/tvm/relay/expr.py"),
                            177, 14)

        run_find_references(server,
                            join_path(tvm_path, "src/relay/ir/expr.cc"),
                            39, 33)

        run_find_definition(server,
                            join_path(tvm_path, "python/tvm/stmt.py"),
                            96, 34)

        run_find_references(server,
                            join_path(tvm_path, "python/tvm/stmt.py"),
                            96, 34)

        run_find_definition(server,
                            join_path(tvm_path, "python/tvm/stmt.py"),
                            56, 18)

        run_find_references(server,
                            join_path(tvm_path, "python/tvm/stmt.py"),
                            56, 18)

        run_find_definition(server,
                            join_path(tvm_path, "src/relay/backend/compile_engine.cc"),
                            730, 59)

        run_find_references(server,
                            join_path(tvm_path, "src/relay/backend/compile_engine.cc"),
                            730, 59)

        # TVM_REGISTER_API("ir_pass.Simplify")
        res = run_find_references(server,
                                  join_path(tvm_path, "src/api/api_pass.cc"),
                                  33, 30)
        assert(len(res) == 6)

        # _pass.Simplify(end - begin)
        res = run_find_references(server,
                                  join_path(tvm_path, "python/tvm/ir_builder.py"),
                                  214, 48)
        assert(len(res) == 6)

        # REGISTER_MAKE(Provide);
        res = run_find_references(server,
                                  join_path(tvm_path, "src/api/api_ir.cc"),
                                  156, 15)
        assert(len(res) == 6)

    #test_real_repo()
    test_dummy_repo()


def test_torch_dialect():
    pytorch_path = os.path.join(curr_path, "..", "dummy_repo", "pytorch")

    server = langserver.BaseServer()
    uri = langserver.path2uri(pytorch_path)
    server.m_initialize(rootUri=uri)

    # ops.quantized.conv2d
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/nn/quantized/modules/conv.py"),
                              38, 28)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("qconv.cpp"))
    assert(res[0]['range']['start']['line'] == 2)

    # torch._C._jit_script_class_compile
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              20, 50)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 126)

    # torch._C.CompilationUnit()
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              25, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 1)
    assert(res[0]['range']['end']['character'] == 27)

    # torch.conv2d
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/nn/functional.py"),
                              16, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_torch_functions.cpp"))
    assert(res[0]['range']['start']['line'] == 2)

    # module._c._create_method_from_trace
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              61, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 105)

    # self._c._get_method(attr)
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              106, 30)

    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 21)

    # self._c._define(self._concrete_type, src, rcb)
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              98, 18)

    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 94)

    # Variable._execution_engine.run_backward
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/autograd/__init__.py"),
                              24, 40)

    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_engine.cpp"))
    assert(res[0]['range']['start']['line'] == 13)

    # _C._FunctionBase._do_forward
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/autograd/function.py"),
                              5, 40)

    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_function.cpp"))
    assert(res[0]['range']['start']['line'] == 11)

    # torch._C._get_qengine()
    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/backends/quantized/__init__.py"),
                              6, 45)

    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("Module.cpp"))
    assert(res[0]['range']['start']['line'] == 46)

def test_mxnet_dialect():
    mx_path = os.path.join(curr_path, "..", "dummy_repo", "mxnet")
    server = langserver.BaseServer()
    uri = langserver.path2uri(mx_path)
    server.m_initialize(rootUri=uri)

    res = run_find_definition(server,
                              join_path(mx_path, "python/mxnet/executor.py"),
                              55, 35)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("c_api_executor.cc"))
    assert(res[0]['range']['start']['line'] == 25)


def test_dgl_dialect():
    dgl_path = os.path.join(curr_path, "..", "dummy_repo", "dgl")
    server = langserver.BaseServer()
    uri = langserver.path2uri(dgl_path)
    server.m_initialize(rootUri=uri)

    res = run_find_definition(server,
                              join_path(dgl_path, "python/dgl/nodeflow.py"),
                              16, 20)
    # assert(len(res) > 0)


def test_taichi_dialect():
    ti_path = os.path.join(curr_path, "..", "dummy_repo", "taichi")
    server = langserver.BaseServer()
    uri = langserver.path2uri(ti_path)
    server.m_initialize(rootUri=uri)

    # ti.core.global_var_expr_from_snode
    res = run_find_definition(server,
                              join_path(ti_path, "python/taichi/lang/snode.py"),
                              4, 40)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_bindings.cpp"))
    assert(res[0]['range']['start']['line'] == 8)

    # taichi_lang_core.create_kernel
    res = run_find_definition(server,
                              join_path(ti_path, "python/taichi/lang/kernel.py"),
                              74, 40)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_bindings.cpp"))
    assert(res[0]['range']['start']['line'] == 11)

    # tc_core.Array2DVector4
    res = run_find_definition(server,
                              join_path(ti_path, "python/taichi/misc/util.py"),
                              34, 40)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("export_math.cpp"))
    assert(res[0]['range']['start']['line'] == 12)

    # core.get_current_program()
    res = run_find_definition(server,
                              join_path(ti_path, "python/taichi/lang/__init__.py"),
                              10, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_bindings.cpp"))
    assert(res[0]['range']['start']['line'] == 15)


if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    test_tvm_dialect()
    test_torch_dialect()
    test_mxnet_dialect()
    test_dgl_dialect()
    test_taichi_dialect()
