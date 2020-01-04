from ffi_navigator import langserver

import logging
import os
from ffi_navigator import workspace


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


def test_tvm_dialect(tvm_path):
    # tested on git tag e69bd1284b50630df570b3a5779a801982203756
    server = langserver.BaseServer()
    server.m_initialize(rootUri=langserver.path2uri(tvm_path))

    run_find_references(server,
                        os.path.join(tvm_path, "python/tvm/api.py"),
                        58, 33)

    run_find_definition(server,
                        os.path.join(tvm_path, "python/tvm/relay/expr.py"),
                        177, 14)

    run_find_references(server,
                        os.path.join(tvm_path, "src/relay/ir/expr.cc"),
                        39, 33)

    run_find_definition(server,
                        os.path.join(tvm_path, "python/tvm/stmt.py"),
                        96, 34)

    run_find_references(server,
                        os.path.join(tvm_path, "python/tvm/stmt.py"),
                        96, 34)

    run_find_definition(server,
                        os.path.join(tvm_path, "python/tvm/stmt.py"),
                        56, 18)

    run_find_references(server,
                        os.path.join(tvm_path, "python/tvm/stmt.py"),
                        56, 18)

    run_find_definition(server,
                        os.path.join(tvm_path, "src/relay/backend/compile_engine.cc"),
                        730, 59)

    run_find_references(server,
                        os.path.join(tvm_path, "src/relay/backend/compile_engine.cc"),
                        730, 59)


def test_torch_dialect(pytorch_path):
    server = langserver.BaseServer()
    uri = langserver.path2uri(pytorch_path)
    server.m_initialize(rootUri=uri)

    res = run_find_definition(server,
                              os.path.join(pytorch_path, "torch/nn/quantized/modules/conv.py"),
                              38, 28)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("qconv.cpp"))
    assert(res[0]['range']['start']['line'] == 2)

    res = run_find_definition(server,
                              os.path.join(pytorch_path, "torch/jit/__init__.py"),
                              20, 50)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("init.cpp"))
    assert(res[0]['range']['start']['line'] == 95)

    res = run_find_definition(server,
                              os.path.join(pytorch_path, "torch/nn/functional.py"),
                              16, 30)
    assert(len(res) > 0)
    assert(res[0]['uri'].endswith("python_torch_functions.cpp"))
    assert(res[0]['range']['start']['line'] == 2)


if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    curr_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
    tvm_path = os.path.abspath(os.path.join(curr_dir, "..", "..", "..", "tvm"))
    if os.path.exists(tvm_path):
        test_tvm_dialect(tvm_path)
    pytorch_path = os.path.join("..", "dummy_repo", "pytorch")
    test_torch_dialect(pytorch_path)
