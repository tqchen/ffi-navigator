from pathlib import Path


def join_path(root_path, relative_path):
    return str(root_path / Path(relative_path))


def normalize_path(raw_path):
    """Convert a unix file path to platform specific one"""
    return join_path("", raw_path)
