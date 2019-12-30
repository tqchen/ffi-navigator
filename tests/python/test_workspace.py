import logging
import os
from ffi_navigator import workspace

def run_check_workspace(tvm_path):
    ws = workspace.Workspace()
    ws.initialize(tvm_path)

    def log_resolve(mod_path, var_name):
        logging.info("Resolve %s -> %s", (mod_path, var_name) , ws.pyimport_resolver.resolve(mod_path, var_name))

    log_resolve("tvm/relay/_expr", "_init_api")
    log_resolve("tvm/relay/expr", "_expr.Let")
    log_resolve("tvm/stmt", "_make")

    def log_packed_def(func_name):
        logging.info("GetDef %s -> %s", func_name, ws.key2defs.get(func_name, []))
    log_packed_def("relay._transform.BackwardFoldScaleAxis")
    log_packed_def("relay.backend.lower")

    def log_find_refs(func_name):
        logging.info("FindRefs %s -> %s", func_name, ws.find_refs(func_name))

    log_find_refs("make.LetStmt")
    log_find_refs("relay.backend.lower")


    def log_find_def(mod, name):
        logging.info("FindDefs %s:%s -> %s", mod, name, ws.find_defs(mod, name))

    log_find_def("tvm/relay/expr", "_make.Call")
    log_find_def("tvm/stmt", "_make.LetStmt")




if __name__ == "__main__":
    # eyeballing test script
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    curr_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
    tvm_path = os.path.abspath(os.path.join(curr_dir, "..", "..", "..", "tvm"))
    if os.path.exists(tvm_path):
        run_check_workspace(tvm_path)
