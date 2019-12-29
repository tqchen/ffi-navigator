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
        self._packed_func_refs = {}
        self._object_defs = {}
        self._object_regs = {}
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
        self._packed_func_refs = {}
        self._object_defs = {}
        self._object_regs = {}
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

    def _update_packed_ref(self, packed_ref_list):
        for item in packed_ref_list:
            if item.full_name in self._packed_func_refs:
                self._packed_func_refs[item.full_name].append(item)
            else:
                self._packed_func_refs[item.full_name] = [item]

    def _update_py(self, path, source):
        mod_path = path[:-3] if path.endswith(".py") else path
        self.pyimport_resolver.update_doc(path, source)
        self._update_packed_def(pattern.find_py_register_packed(path, source))

        for item in pattern.find_py_register_object(path, source):
            self._object_regs[item.full_name] = [ item ]

        # _init_api information
        init_api_list = pattern.find_py_init_api(source)
        if init_api_list:
            init_api_list = [
                x[4:] if x.startswith("tvm.") else x for x in init_api_list]
            self._modpath2initapi[mod_path] = init_api_list

    def _update_cc(self, path, source):
        reg_packed = pattern.find_cc_register_packed(path, source)
        self._update_packed_def(reg_packed)
        self._update_packed_ref(reg_packed)
        self._update_packed_ref(pattern.find_cc_get_packed(path, source))
        for item in pattern.find_cc_decl_object(path, source):
            self._object_defs[item.full_name] = [ item ]

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

    def _py_has_valid_init_api(self, mod_path):
        if mod_path == self._pypath_api_internal:
            return True
        new_mod, new_name = self.pyimport_resolver.resolve(mod_path, "_init_api")
        return new_mod == self._pypath_funcmod and new_name == "_init_api"

    def find_definition(self, mod_path, sym_name):
        """Get definition given mod path and symbol name"""
        self._sync_states()
        mod_path, var_name = self.pyimport_resolver.resolve(mod_path, sym_name)

        if var_name is None:
            return []

        if mod_path == self._pypath_api_internal:
            prefix_lst = [""]
        else:
            prefix_lst = self._modpath2initapi.get(mod_path, [])
            if prefix_lst and not self._py_has_valid_init_api(mod_path):
                prefix_lst = []
            prefix_lst = [x + "." for x in prefix_lst]

        for prefix in prefix_lst:
            opt1 = prefix + var_name
            res = self.get_packed_def(opt1)
            if res:
                return res
        return []

    def _py_find_packed_refs(self, func_name):
        # Step 1: find python ffi module that import the related function
        var_targets = set()
        mod_targets = {}
        if func_name.startswith("_"):
            mod_path = self._pypath_api_internal
            var_targets.add((mod_path, func_name))
            mod_targets[mod_path] = func_name
        else:
            for mod_path, prefix_list in self._modpath2initapi.items():
                if not self._py_has_valid_init_api(mod_path):
                    continue
                for prefix in prefix_list:
                    if func_name.startswith(prefix):
                        local_name = func_name[len(prefix)+1:]
                        var_targets.add((mod_path, local_name))
                        mod_targets[mod_path] = local_name
        # Step2: find modules that imports the ffi modules
        #        construct search terms
        search_map = {}
        for mod_path, var_list in self.pyimport_resolver._modpath2imports.items():
            search_term = []
            for var_name in var_list:
                new_path, new_var = self.pyimport_resolver.resolve(mod_path, var_name)
                if (new_path, new_var) in var_targets:
                    search_term.append(var_name)
                if new_var is None and new_path in mod_targets:
                    search_term.append(var_name + "." + mod_targets[new_path])
            if search_term:
                search_map[mod_path] = search_term
        # Step 3: search the related files
        results = []
        for mod_path, terms in search_map.items():
            if not mod_path.endswith(".py"):
                mod_path += ".py"
            if os.path.isfile(mod_path):
                res = pattern.search_symbol(open(mod_path).read(), terms)
                for x in res:
                    results.append(pattern.PackedFuncRef(
                        path=mod_path,
                        full_name=func_name,
                        range=x))
        return results

    def find_packed_refs(self, func_name):
        self._sync_states()
        res = self._py_find_packed_refs(func_name)
        res += self._packed_func_refs.get(func_name, [])
        return res
