"""Base class for providers"""
import os
from .. import pattern
from ..util import normalize_path


class BaseProvider(object):
    """Base class for dialect specific providers.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object

    dialect_name : str
        The name of derived dialect (tvm, torch etc)
    """
    def __init__(self, resolver, logger, dialect_name):
        self.resolver = resolver
        self._pypath_root = None
        self.logger = logger
        self.dialect_name = dialect_name

    def get_additional_scan_dirs(self, root_path):
        """If the repository structure is not organized as src, include, python,
        override this method to register specific directories.
        See Torch dialect for example.
        """
        return []

    def init_pass(self, path, source):
        """This function will be called for each file before extract."""
        if path.endswith(normalize_path("%s/__init__.py" % self.dialect_name)):
            self._pypath_root = os.path.abspath(path[:-len("/__init__.py")])
            self.resolver.add_package(self.dialect_name, self._pypath_root)
            self.logger.info("%s: found python path %s", self.dialect_name, self._pypath_root)

    def _cc_extract(self, path, source, begin, end):
        """Override this method in the derived class."""
        return []

    def _py_extract(self, path, source, begin, end):
        """Override this method in the derived class."""
        return []

    def extract(self, path, source, begin=0, end=None):
        """This function will be called for each file
        Extract patterns in the file as specified in pattern.py and return them.
        """
        cpp_ext = [".cpp", ".cc", ".h"]
        for ext in cpp_ext:
            if path.endswith(ext):
                return self._cc_extract(path, source, begin, end)
        if path.endswith(".py"):
            return self._py_extract(path, source, begin, end)
        return []

    def extract_symbol(self, path, source, pos):
        """Extract possible pattern in the specified location, if not found, return None."""
        # only search a small context
        begin = max(pos.line - 1, 0)
        end = min(pos.line + 2, len(source))
        for res in self.extract(path, source, begin, end):
            if (isinstance(res, (pattern.Ref, pattern.Def)) and
                res.range.start.line <= pos.line and
                res.range.end.line >= pos.line and
                res.range.start.character <= pos.character and
                res.range.end.character >= pos.character):
                return res
        return None
