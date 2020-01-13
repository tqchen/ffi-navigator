import sys
from pathlib import Path


def is_win():
    return sys.platform == "win32"


def join_path(root_path, relative_path):
    """Join the two path taking into account the platform difference
    Each path can be a unix file path and the joined path works on Windows
    Alternative for os.path.join
    """
    return str(Path(root_path) / Path(relative_path))


def normalize_path(raw_path):
    """Convert a unix file path to platform specific one"""
    return join_path("", raw_path)
