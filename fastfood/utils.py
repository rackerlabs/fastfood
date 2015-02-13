"""fastfood utils."""

import os


def normalize_path(path):
    """Normalize and return absolute path.

    Expand user symbols like ~ and resolve relative paths.
    """
    return os.path.abspath(os.path.expanduser(os.path.normpath(path)))


def ruby_strip(chars):
    """Strip whitespace and any quotes."""
    return chars.strip(' "\'')


def ruby_lines(text):
    """Tidy up lines from a file, honor # comments.

    Does not honor ruby block comments (yet).
    """
    if isinstance(text, basestring):
        text = text.splitlines()
    elif not isinstance(text, list):
        raise TypeError("text should be a list or a string, not %s"
                        % type(text))
    return [l.strip() for l in text if l.strip()
            and not l.strip().startswith('#')]
