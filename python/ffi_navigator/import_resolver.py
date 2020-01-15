"""A resolver to resolve expression to the original definition point."""
import os
import logging
from .pattern import find_py_imports
from .util import normalize_path
from typing import Dict, List, Tuple

def _num_leading_dots(path):
    for i, val in enumerate(path):
        if val != ".":
            return i
    return len(path)


class PyImportResolver:
    """Resolve the original module path and sym_name."""
    def __init__(self):
        self._modpath2imports = {}
        self._modpath2init = {}
        self._pkg2modpath = {}
        self._recurr_depth = 0

    def add_package(self, package, mod_path):
        """Add root path of a package to the resolver.

        This will enable absolute import of the package

        Parameters
        ----------
        package : str
            The name of the package

        mod_path : str
            The path to the package
        """
        self._pkg2modpath[package] = mod_path

    def resolve(self, mod_path, attr_name):
        """Try to resolve an attribute expression to its original definition point.

        Parameters
        ----------
        mod_path: str
            Path to the module

        attr_name: str
            The attr name, can contain multiple dots(".")

        Returns
        -------
        mod_path: str
            The resolve path.

        sym_name: Optional[str]
            The resolved name, can be None if it is a module.
        """
        # lookup packages
        if not mod_path.startswith(normalize_path("/")):
            arr = mod_path.split(normalize_path("/"), 1)
            if arr[0] in self._pkg2modpath:
                arr[0] = self._pkg2modpath[arr[0]]
            mod_path = normalize_path("/".join(arr))
        # canonicalize
        if mod_path.endswith(".py"):
            mod_path = mod_path[:-3]

        self._recurr_depth = 0
        arr = attr_name.split(".", 1)
        if len(arr) == 1:
            return self._resolve_var(mod_path, arr[0], allow_combine_path=False)
        new_mod, new_var = self._resolve_var(
            mod_path, arr[0], allow_combine_path=False)
        if new_var is None:
            return self.resolve(new_mod, arr[1])
        # Failed to resolve further
        return (mod_path, attr_name)

    def _resolve_var(self, mod_path, var_name, allow_combine_path=True):
        """Resolve from mod_path import var_name"""
        # Avoid deep recursion
        self._recurr_depth += 1
        if self._recurr_depth > 10:
            return (mod_path, var_name)
        # First check whether we can resolve to a module
        if allow_combine_path:
            combined_path = os.path.join(mod_path, var_name)
            if (combined_path in self._modpath2imports or
                combined_path in self._modpath2init):
                return (combined_path, None)
        # mod/ -> mod/__init__
        if mod_path in self._modpath2init:
            mod_path = self._modpath2init[mod_path]
        if mod_path not in self._modpath2imports:
            return (mod_path, var_name)
        # Check the imports
        imports = self._modpath2imports[mod_path]
        if var_name in imports:
            new_mod, new_var = imports[var_name]
            if new_var is None:
                return (new_mod, new_var)
            return self._resolve_var(new_mod, new_var)
        return (mod_path, var_name)

    def _resolve_mod_path(self, curr_dir, from_mod):
        """Resolve new mod path given the location indicated in from_mod"""
        ndots = _num_leading_dots(from_mod)
        arr = from_mod[ndots:].split(".")
        if ndots != 0:
            prev = [".."] * (ndots - 1)
            return os.path.abspath(os.path.join(curr_dir, *prev, normalize_path("/".join(arr))))
        if arr[0] in self._pkg2modpath:
            return os.path.abspath(
                os.path.join(self._pkg2modpath[arr[0]], normalize_path("/".join(arr[1:]))))
        return os.path.abspath(os.path.join(curr_dir, normalize_path("/".join(arr))))

    def update_doc(self, path, source):
        """Update the resolver state by adding a document.

        Parameters
        ----------
        path : str
            The module path

        source : list or str
            The source code.
        """
        path = os.path.abspath(path)
        if path.endswith(".py"):
            path = path[:-3]
        imports = {}
        for item in find_py_imports(source):
            target_mod = self._resolve_mod_path(
                os.path.dirname(path), item.from_mod)
            if target_mod is not None:
                alias = item.alias if item.alias else item.import_name
                imports[alias] = (target_mod, item.import_name)
        self._modpath2imports[path] = imports
        init = normalize_path("/__init__")
        if path.endswith(init):
            self._modpath2init[path[:-len(init)]] = path
