import logging
import os
from tvm_ffi_navigator import workspace

def run_check_workspace(tvm_path):
    ws = workspace.Workspace()
    ws.initialize(tvm_path)
    def log_resolve(mod_path, var_name):
        logging.info("Resolve %s -> %s", (mod_path, var_name) , ws.pyimport_resolver.resolve(mod_path, var_name))
    log_resolve("tvm/relay/_expr", "_init_api")
    log_resolve("tvm/relay/expr", "_expr.Let")
    log_resolve("tvm/stmt", "_make")

    def log_packed_decl(func_name):
        logging.info("PackedDef %s -> %s", func_name, ws.packed_func_defs.get(func_name, None))
    log_packed_decl("relay._transform.BackwardFoldScaleAxis")
    logging.info("%s", ws.get_definition("tvm/relay/expr", "_make.Call"))

    logging.info("%s", ws.get_definition("tvm/stmt", "_make.LetStmt"))

if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    curr_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
    tvm_path = os.path.abspath(os.path.join(curr_dir, "..", "..", "..", "tvm"))
    if os.path.exists(tvm_path):
        run_check_workspace(tvm_path)

