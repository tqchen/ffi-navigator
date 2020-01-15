from ffi_navigator import langserver
from ffi_navigator.util import join_path

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

        res = run_find_definition(server,
                                  join_path(tvm_path, "python/tvm/relay/expr.py"),
                                  15, 14)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("expr.h"))
        assert(res[0]['range']['start']['line'] == 33)

        res = run_find_definition(server,
                                  join_path(tvm_path, "python/tvm/stmt.py"),
                                  26, 30)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("api_ir.cc"))
        assert(res[0]['range']['start']['line'] == 14)

        res = run_find_definition(server,
                                  join_path(tvm_path, "python/tvm/stmt.py"),
                                  46, 20)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("api_ir.cc"))
        assert(res[0]['range']['start']['line'] == 15)

        # lookup relay.backend.lower from c++ to python
        res = run_find_definition(server,
                                  join_path(tvm_path, "src/relay/backend/compile_engine.cc"),
                                  74, 59)
        assert(len(res) == 1)
        assert(res[0]['uri'].endswith("_backend.py"))
        assert(res[0]['range']['start']['line'] == 8)

        # res = run_find_references(server,
        #                           join_path(tvm_path, "include/tvm/expr.h"),
        #                           15, 49)
        # assert(len(res) == 2)
        # assert(res[1]['uri'].endswith("expr.py"))
        # assert(res[1]['range']['start']['line'] == 15)

        # res = run_find_references(server,
        #                           join_path(tvm_path, "python/tvm/api.py"),
        #                           24, 33)
        # assert(len(res) == 2)
        # assert(res[0]['uri'].endswith("api_lang.cc"))
        # assert(res[0]['range']['start']['line'] == 15)

    def test_real_repo():
        # tested on tvm git tag e69bd1284b50630df570b3a5779a801982203756
        tvm_path = os.path.join(curr_path, "..", "..", "..", "tvm")
        if not os.path.exists(tvm_path):
            logging.info("Skip tvm tests")
            return

        server = langserver.BaseServer()
        server.m_initialize(rootUri=langserver.path2uri(tvm_path))

        # run_find_references(server,
        #                     join_path(tvm_path, "include/tvm/expr.h"),
        #                     119, 49)

        # run_find_references(server,
        #                     join_path(tvm_path, "python/tvm/api.py"),
        #                     58, 33)

        # run_find_definition(server,
        #                     join_path(tvm_path, "python/tvm/relay/expr.py"),
        #                     177, 14)

        # run_find_references(server,
        #                     join_path(tvm_path, "src/relay/ir/expr.cc"),
        #                     39, 33)
        # print("run find def")
        # run_find_definition(server,
        #                     join_path(tvm_path, "python/tvm/stmt.py"),
        #                     96, 34)

        # run_find_references(server,
        #                     join_path(tvm_path, "python/tvm/stmt.py"),
        #                     96, 34)

        # run_find_definition(server,
        #                     join_path(tvm_path, "python/tvm/stmt.py"),
        #                     56, 18)

        # run_find_references(server,
        #                     join_path(tvm_path, "python/tvm/stmt.py"),
        #                     56, 18)

        run_find_definition(server,
                            join_path(tvm_path, "src/relay/backend/compile_engine.cc"),
                            727, 59)

        # run_find_references(server,
        #                     join_path(tvm_path, "src/relay/backend/compile_engine.cc"),
        #                     727, 59)

    test_dummy_repo()
    # test_real_repo()

def test_torch_dialect():
    pytorch_path = os.path.join(curr_path, "..", "dummy_repo", "pytorch")

    server = langserver.BaseServer()
    uri = langserver.path2uri(pytorch_path)
    server.m_initialize(rootUri=uri)

    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/nn/quantized/modules/conv.py"),
                              38, 28)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("qconv.cpp"))
    assert(res[0]['range']['start']['line'] == 2)

    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              20, 50)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 95)

    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/jit/__init__.py"),
                              25, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 1)
    assert(res[0]['range']['end']['character'] == 27)

    res = run_find_definition(server,
                              join_path(pytorch_path, "torch/nn/functional.py"),
                              16, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_torch_functions.cpp"))
    assert(res[0]['range']['start']['line'] == 2)


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


if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    test_tvm_dialect()
    # test_torch_dialect()
    # test_mxnet_dialect()
    # test_dgl_dialect()
