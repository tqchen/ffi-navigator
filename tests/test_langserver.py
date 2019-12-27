from tvm_ffi_navigator import langserver

import logging
import os
from tvm_ffi_navigator import workspace

def run_check_langserver(tvm_path):
    server = langserver.BaseServer()
    uri = langserver.path2uri(tvm_path)
    server.m_initialize(rootUri=uri)
    stmt_uri = langserver.path2uri(os.path.join(tvm_path, "python/tvm/stmt.py"))
    ret1 = server.m_text_document__definition(
        **{'textDocument': {'uri': stmt_uri}, 'position': {'line': 96, 'character': 34}})

    ret0 = server.m_text_document__definition(
        textDocument={"uri": stmt_uri},
        position={"line": 56, "character": 18 })


if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    curr_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
    tvm_path = os.path.abspath(os.path.join(curr_dir, "..", "..", "..", "tvm"))
    if os.path.exists(tvm_path):
        run_check_langserver(tvm_path)
