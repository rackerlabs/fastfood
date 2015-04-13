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
from __future__ import print_function

import copy
import os
import StringIO


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
    return [l.strip() for l in text if l.strip() and not
            l.strip().startswith('#')]


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


class FileWrapper(object):

    """Helps wrap ruby files, usually.

    Like metadata.rb and Berksfile.
    """

    def __init__(self, stream):
        """Requires a file-like object."""

        self.stream = stream

    @classmethod
    def from_string(cls, contents):
        """Initialize class with a string."""
        stream = StringIO.StringIO(contents)
        return cls(stream)

    def __str__(self):
        """String representation of the object."""
        return '%s(%s)' % (type(self).__name__, self.stream)

    def __repr__(self):
        """Canonical string representation of the object."""
        return ('<%s [%r] at %s>' % (type(self).__name__,
                                     self.stream,
                                     hex(id(self))))

    def __getattr__(self, attr):
        try:
            return getattr(self.stream, attr)
        except AttributeError:
            raise AttributeError("'%s' object has no attribute '%s'"
                                 % (type(self).__name__, attr))

    def write_statements(self, statements):
        """Insert the statements into the file neatly.

        Ex:

        statements = ["good  'dog'", "good 'cat'", "bad  'rat'", "fat 'emu'"]

        # stream.txt ... animals = FileWrapper(open('stream.txt'))
        good 'cow'
        nice 'man'
        bad 'news'

        animals.write_statements(statements)

        # stream.txt
        good 'cow'
        good 'dog'
        good 'cat'
        nice 'man'
        bad 'news'
        bad 'rat'
        fat 'emu'
        """
        self.seek(0)
        original_content_lines = self.readlines()
        new_content_lines = copy.copy(original_content_lines)
        # ignore blanks and sort statements to be written
        statements = sorted([stmnt for stmnt in statements if stmnt])

        # find all the insert points for each statement
        uniqs = {stmnt.split(None, 1)[0] for stmnt in statements}
        insert_locations = {}
        for line in reversed(original_content_lines):
            if not uniqs:
                break
            if not line:
                continue
            for word in uniqs.copy():
                if line.startswith(word):
                    index = original_content_lines.index(line) + 1
                    insert_locations[word] = index
                    uniqs.remove(word)

        for statement in statements:
            print("writing to %s : %s" % (self, statement))
            startswith = statement.split(None, 1)[0]
            # insert new statement with similar OR at the end of the file
            new_content_lines.insert(
                insert_locations.get(startswith, len(new_content_lines)),
                statement)

        if new_content_lines != original_content_lines:
            self.seek(0)
            self.writelines(new_content_lines)
            self.flush()
