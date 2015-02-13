# Copyright 2015 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fastfood utils."""

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


def deepupdate(original, update, levels=5):
    """Update, like dict.update, but deeper.

    Update 'original' from dict/iterable 'update'.

    I.e., it recurses on dicts 'levels' times if necessary.

    A standard dict.update is levels=0
    """
    if not isinstance(update, dict):
        update = dict(update)
    if not levels > 0:
        original.update(update)
    else:
        for key, val in update.iteritems():
            if isinstance(original.get(key), dict):
                # might need a force=True to override this
                if not isinstance(val, dict):
                    raise TypeError("Trying to update dict %s with "
                                    "non-dict %s" % (original[key], val))
                deepupdate(original[key], val, levels=levels-1)
            else:
                original.update({key: val})
