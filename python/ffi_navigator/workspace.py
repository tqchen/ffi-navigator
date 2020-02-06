import glob
import os
import logging
from . import pattern
from .import_resolver import PyImportResolver
from .dialect import autodetect_dialects
from .util import join_path


def _append_dict(sdict, key, value):
    if key in sdict:
        sdict[key].append(value)
    else:
        sdict[key] = [value]

class Workspace:
    """Analysis workspace"""
    def __init__(self, logger=None):
        # logger
        self.logger = logging if logger is None else logger
        # states
        self.pyimport_resolver = PyImportResolver()
        self.key2defs = {}
        self.key2refs = {}
        self.modpath2exports = {}
        self._need_reload = False
        # information
        self._root_path = None

    def initialize(self, root_path):
        # By default only update root/src, root/python, root/include
        # can add configs later
        self.logger.info("root_path: %s", root_path)
        self._providers = autodetect_dialects(root_path, self.pyimport_resolver, self.logger)
        self._root_path = root_path
        self._reload()

    def _reload(self):
        """Reload workspace."""
        self.key2defs = {}
        self.key2refs = {}
        self.modpath2exports = {}
        scan_dirs = [
            os.path.join(self._root_path, "src"),
            os.path.join(self._root_path, "include"),
            os.path.join(self._root_path, "python")
        ]
        for provider in self._providers:
            scan_dirs += provider.get_additional_scan_dirs(self._root_path)
        for dirname in scan_dirs:
            self.update_dir(dirname)
        self._need_reload = False

    def _sync_states(self):
        """Synchronize the workspace states."""
        if self._need_reload:
            self._reload()

    def init_pass(self, path, source):
        """Initialization pass"""
        mod_path = path[:-3] if path.endswith(".py") else path
        self.pyimport_resolver.update_doc(path, source)
        for provider in self._providers:
            provider.init_pass(path, source)

    def update_dir(self, dirname):
        self.logger.info("Workspace.update_dir %s start", dirname)
        # intialize pass
        for path in sorted(glob.glob(join_path(dirname, "**/*.py"), recursive=True)):
            self.init_pass(path, open(path).readlines())
        # normal scans
        for path in sorted(glob.glob(join_path(dirname, "**/*.py"), recursive=True)):
            self.update_doc(path, open(path).readlines())
        for path in sorted(glob.glob(join_path(dirname, "**/*.h"), recursive=True)):
            self.update_doc(path, open(path).readlines())
        for path in sorted(glob.glob(join_path(dirname, "**/*.cc"), recursive=True)):
            self.update_doc(path, open(path).readlines())
        for path in sorted(glob.glob(join_path(dirname, "**/*.cpp"), recursive=True)):
            self.update_doc(path, open(path).readlines())
        self.logger.info("Workspace.update_dir %s finish", dirname)

    def update_doc(self, path, source):
        for provider in self._providers:
            for pt in provider.extract(path, source):
                mod_path = path[:-3] if path.endswith(".py") else path
                if isinstance(pt, pattern.Def):
                    _append_dict(self.key2defs, pt.key, pt)
                elif isinstance(pt, pattern.Ref):
                    _append_dict(self.key2refs, pt.key, pt)
                elif isinstance(pt, pattern.Export):
                    _append_dict(self.modpath2exports, mod_path, pt)
                else:
                    self.logger.warn("Ignore pattern %s, path=%s", pt, path)
        self.logger.debug("Workspace.update_doc %s", path)

    def find_defs(self, mod_path, sym_name):
        """Get definition given python mod path and symbol name"""
        self._sync_states()
        mod_path, var_name = self.pyimport_resolver.resolve(mod_path, sym_name)
        if var_name is None:
            return []

        export_list = self.modpath2exports.get(mod_path, [])

        for item in export_list:
            key = item.fvar2key(var_name)
            if key in self.key2defs:
                return self.key2defs[key]
        return []

    def _py_find_refs(self, key):
        # Step 1: find python ffi module that import the related function
        var_targets = set()
        mod_targets = {}

        for mod_path, exports in self.modpath2exports.items():
            for item in exports:
                if key.startswith(item.key_prefix):
                    var_name = item.fkey2var(key)
                    var_targets.add((mod_path, var_name))
                    mod_targets[mod_path] = var_name

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

        for mod_path, var_name in mod_targets.items():
            search_map[mod_path] = [var_name]

        # Step 3: search the related files
        results = []
        for mod_path, terms in search_map.items():
            path = mod_path if mod_path.endswith(".py") else mod_path + ".py"
            if os.path.isfile(path):
                res = pattern.search_symbol(open(path).read(), terms)
                for x in res:
                    results.append(pattern.Ref(key=key, path=path, range=x))
        return results

    def find_refs(self, key):
        self._sync_states()
        res = self._py_find_refs(key)
        res += self.key2refs.get(key, [])
        return res

    def extract_symbol(self, path, source, pos):
        for pt in self._providers:
            res = pt.extract_symbol(path, source, pos)
            if res:
                return res
        return pattern.extract_symbol(source, pos)
