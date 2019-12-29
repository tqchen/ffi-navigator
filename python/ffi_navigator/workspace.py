import glob
import os
import logging
from . import pattern
from .import_resolver import PyImportResolver

class Workspace:
    """Analysis workspace"""
    def __init__(self, logger=None):
        # states
        self.pyimport_resolver = PyImportResolver()
        self._packed_func_defs = {}
        self._modpath2initapi = None
        self._need_reload = False
        # logger
        self.logger = logging if logger is None else logger
        # information
        self._root_path = None
        self._pypath_root = None
        self._pypath_funcmod = None
        self._pypath_api_internal = None

    def initialize(self, root_path):
        # By default only update root/src, root/python, root/include
        # can add configs later
        self._root_path = root_path
        self._reload()

    def _reload(self):
        """Reload workspace."""
        self.pyimport_resolver = PyImportResolver()
        self._packed_func_defs = {}
        self._modpath2initapi = {}
        self.update_dir(os.path.join(self._root_path, "src"))
        self.update_dir(os.path.join(self._root_path, "include/tvm"))
        self.update_dir(os.path.join(self._root_path, "python/tvm"))
        self._need_reload = False

    def _sync_states(self):
        """Synchronize the workspace states."""
        if self._need_reload:
            self._reload()

    def update_dir(self, dirname):
        logging.info("Workspace.update_dir %s start", dirname)
        for path in sorted(glob.glob(os.path.join(dirname, "**/*.py"), recursive=True)):
            self.update_doc(os.path.abspath(path), open(path).readlines())
        for path in sorted(glob.glob(os.path.join(dirname, "**/*.h"), recursive=True)):
            self.update_doc(os.path.abspath(path), open(path).readlines())
        for path in sorted(glob.glob(os.path.join(dirname, "**/*.cc"), recursive=True)):
            self.update_doc(os.path.abspath(path), open(path).readlines())
        logging.info("Workspace.update_dir %s finish", dirname)

    def update_doc(self, path, source):
        # update special path
        if path.endswith("python/tvm/__init__.py"):
            self._pypath_root = os.path.abspath(path[:-len("/__init__.py")])
            self._pypath_funcmod = os.path.join(self._pypath_root, "_ffi", "function")
            self._pypath_api_internal = os.path.join(self._pypath_root, "_api_internal")
            self.pyimport_resolver._pkg2modpath["tvm"] = self._pypath_root
            logging.info("Set tvm python path %s", self._pypath_root)
        # update resolver
        if path.endswith(".py"):
            self._update_py(path, source)
         # update c++ file
        if path.endswith(".cc") or path.endswith(".h"):
            self._update_cc(path, source)
        logging.debug("Workspace.update_doc %s", path)

    def _update_packed_def(self, packed_reg_list):
        for item in packed_reg_list:
            if item.full_name in self._packed_func_defs:
                self._packed_func_defs[item.full_name].append(item)
            else:
                self._packed_func_defs[item.full_name] = [item]

    def _update_py(self, path, source):
        mod_path = path[:-3] if path.endswith(".py") else path
        self.pyimport_resolver.update_doc(path, source)
        self._update_packed_def(pattern.find_py_register_packed(path, source))
        # _init_api information
        init_api_list = pattern.find_py_init_api(source)
        if init_api_list:
            self._modpath2initapi[mod_path] = init_api_list

    def _update_cc(self, path, source):
        for item in pattern.find_cc_register_packed(path, source):
            if item.full_name in self._packed_func_defs:
                self._packed_func_defs[item.full_name].append(item)
            else:
                self._packed_func_defs[item.full_name] = [item]

    def get_packed_def(self, func_name):
        """Get the packed function defintion for a given function name."""
        self._sync_states()

        def valid(reg):
            if reg.py_reg_func:
                mod, name = self.pyimport_resolver.resolve(reg.path, reg.py_reg_func)
                return mod == self._pypath_funcmod and name == "register_func"
            return True

        if func_name in self._packed_func_defs:
            return [x for x in self._packed_func_defs[func_name] if valid(x)]
        return []

    def get_definition(self, mod_path, sym_name):
        """Get definition given mod path and symbol name"""
        self._sync_states()
        mod_path, var_name = self.pyimport_resolver.resolve(mod_path, sym_name)

        if var_name is None:
            return []

        prefix_lst = self._modpath2initapi.get(mod_path, [])

        def valid_init_api():
            mod, name = self.pyimport_resolver.resolve(mod_path, "_init_api")
            return mod == self._pypath_funcmod

        if prefix_lst and not valid_init_api():
            prefix_lst = []


        # always defer the evaluation.
        if mod_path == self._pypath_api_internal:
            prefix_lst = [""]
        else:
            prefix_lst = [x + "." for x in prefix_lst]
            prefix_lst = [x[4:] if x.startswith("tvm.") else x for x in prefix_lst]


        for prefix in prefix_lst:
            opt1 = prefix + var_name
            res = self.get_packed_def(opt1)
            if res:
                return res
        return []
