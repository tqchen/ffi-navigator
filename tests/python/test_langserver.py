from ffi_navigator import langserver

import logging
import os
from ffi_navigator import workspace

def run_check_langserver(tvm_path):
    server = langserver.BaseServer()
    uri = langserver.path2uri(tvm_path)
    server.m_initialize(rootUri=uri)

    uri = langserver.path2uri(os.path.join(tvm_path, "python/tvm/api.py"))
    server.m_text_document__references(
        textDocument={"uri": uri},
        position={"line": 58, "character": 33 })

    uri = langserver.path2uri(os.path.join(tvm_path, "python/tvm/relay/expr.py"))
    server.m_text_document__definition(
        textDocument={"uri": uri},
        position={"line": 177, "character": 14 })

    uri = langserver.path2uri(os.path.join(tvm_path, "src/relay/ir/expr.cc"))
    server.m_text_document__references(
        textDocument={"uri": uri},
        position={"line": 39, "character": 33 })

    uri = langserver.path2uri(os.path.join(tvm_path, "python/tvm/stmt.py"))
    ret1 = server.m_text_document__definition(
        **{'textDocument': {'uri': uri}, 'position': {'line': 96, 'character': 34}})
    ret1 = server.m_text_document__references(
        **{'textDocument': {'uri': uri}, 'position': {'line': 96, 'character': 34}})

    server.m_text_document__references(
        textDocument={"uri": uri},
        position={"line": 56, "character": 18 })

    ret0 = server.m_text_document__definition(
        textDocument={"uri": uri},
        position={"line": 56, "character": 18 })

    uri = langserver.path2uri(os.path.join(tvm_path, "src/relay/backend/compile_engine.cc"))
    server.m_text_document__definition(
        textDocument={"uri": uri},
        position={"line": 730, "character": 59 })

    server.m_text_document__references(
        textDocument={"uri": uri},
        position={"line": 730, "character": 59 })




if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    curr_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
    tvm_path = os.path.abspath(os.path.join(curr_dir, "..", "..", "..", "tvm"))
    if os.path.exists(tvm_path):
        run_check_langserver(tvm_path)
