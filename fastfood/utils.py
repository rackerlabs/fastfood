"""fastfood utils."""

import os


def normalize_path(path):
    """Normalize and return absolute path.

    Expand user symbols like ~ and resolve relative paths.
    """
    return os.path.abspath(os.path.expanduser(os.path.normpath(path)))
