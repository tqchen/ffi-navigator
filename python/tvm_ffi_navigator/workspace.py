import glob
import os
import logging
from . import pattern
from .import_resolver import PyImportResolver

class Workspace:
    """Analysis workspace"""
    def __init__(self, logger=None):
        self.pyimport_resolver = PyImportResolver()
        self.packed_func_defs = {}
        self.logger = logging if logger is None else logger
        self._modpath2initapi = {}
        self._pypath_root = None
        self._pypath_funcmod = None
        self._pypath_api_internal = None

    def initialize(self, root_path):
        # By default only update root/src, root/python, root/include
        # can add configs later
        self.update_dir(os.path.join(root_path, "src"))
        self.update_dir(os.path.join(root_path, "include/tvm"))
        self.update_dir(os.path.join(root_path, "python/tvm"))

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

    def _update_py(self, path, source):
        self.pyimport_resolver.update_doc(path, source)
        init_api = pattern.find_init_api(source)
        mod_path = path[:-3] if path.endswith(".py") else path
        if init_api:
            self._modpath2initapi[mod_path] = init_api

    def _update_cc(self, path, source):
        for item in pattern.find_register_packed(path, source):
            if item.full_name in self.packed_func_defs:
                self.packed_func_defs[item.full_name].append(item)
            else:
                self.packed_func_defs[item.full_name] = [item]

    def _validate_init_api(self, mod_path):
        mod, name = self.pyimport_resolver.resolve(mod_path, "_init_api")
        return mod == self._pypath_funcmod

    def get_definition(self, mod_path, sym_name):
        """Get definition given mod path and symbol name"""
        mod_path, var_name = self.pyimport_resolver.resolve(mod_path, sym_name)
        if var_name is None:
            return []
        prefix_lst = self._modpath2initapi.get(mod_path, [])
        if mod_path == self._pypath_api_internal:
            prefix_lst = [""]
        elif self._validate_init_api(mod_path):
            prefix_lst = [x + "." for x in prefix_lst]
            prefix_lst = [x[4:] if x.startswith("tvm.") else x for x in prefix_lst]
        else:
            return []

        for prefix in prefix_lst:
            opt1 = prefix + var_name
            if opt1 in self.packed_func_defs:
                return self.packed_func_defs[opt1]
        return []