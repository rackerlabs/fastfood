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

"""Fastfood Chef Cookbook manager."""

import copy
import os
import StringIO

from fastfood import utils


class CookBook(object):

    def __init__(self, path):
        self.path = utils.normalize_path(path)
        self._metadata = None
        if not os.path.isdir(path):
            raise ValueError("Cookbook dir %s does not exist."
                             % self.path)
        self.metadata_path = os.path.join(self.path, 'metadata.rb')
        if not os.path.isfile(self.metadata_path):
            raise ValueError("Cookbook needs metadata.rb, %s"
                             % self.metadata_path)
        self._berksfile = None
        self.berks_path = os.path.join(self.path, 'Berksfile')

    @property
    def metadata(self):
        """Return dict representation of this cookbook's metadata.rb ."""
        if not self._metadata:
            self._metadata = self._parse_metadata()
        return self._metadata

    @property
    def berksfile(self):
        """Return dict representation of this cookbook's Berksfile."""
        if not self._berksfile:
            if not os.path.isfile(self.berks_path):
                raise ValueError("No Berksfile found at %s"
                                 % self.berks_path)
            with open(self.berks_path) as berks:
                self._berksfile = Berksfile(berks)
        return self._berksfile

    def _parse_metadata(self):
        """Open metadata.rb and generate useful map."""
        assert os.path.isfile(self.metadata_path), "metadata.rb not found"
        with open(self.metadata_path) as meta:
            data = utils.ruby_lines(meta.readlines())
        data = [tuple(j.strip() for j in line.split(None, 1))
                for line in data]
        depends = {}
        for line in data:
            if not len(line) == 2:
                continue
            key, value = line
            if key == 'depends':
                value = value.split(',')
                lib = utils.ruby_strip(value[0])
                detail = [utils.ruby_strip(j) for j in value[1:]]
                depends[lib] = detail
        data = {key: utils.ruby_strip(val) for key, val in data}
        if depends:
            data['depends'] = depends
        return data

    def write_metadata_dependencies(self, dependencies):
        """Insert new 'depends' statements and return parsed metadata."""
        if not dependencies:
            return self.metadata
        assert os.path.isfile(self.metadata_path), "metadata.rb not found"
        assert isinstance(dependencies, list), "not a list"
        with open(self.metadata_path, 'r+') as meta:
            orig_content = meta.readlines()
            new_content = copy.copy(orig_content)
            for line in reversed(orig_content):
                if line.startswith('depends'):
                    where = orig_content.index(line) + 1
                    break
            else:  # they should have called it elifnobreak:
                where = len(orig_content)

            for dep in dependencies:
                print "writing to metadata.rb : %s" % dep
                new_content.insert(where, dep)
            if new_content != orig_content:
                meta.seek(0)
                meta.writelines(new_content)
        # reset self.metadata property
        self._metadata = None
        return self.metadata


class Berksfile(object):

    """Wrapper for a Berksfile."""

    berks_options = [
        'branch',
        'git',
        'path',
        'ref',
        'revision',
        'tag',
    ]

    def __init__(self, stream):
        """Requires a file-like object."""

        self.stream = stream

    @classmethod
    def from_string(cls, contents):
        stream = StringIO.StringIO(contents)
        return cls(stream)

    def __getattr__(self, attr):
        try:
            return getattr(self.stream, attr)
        except AttributeError:
            raise AttributeError("'Berksfile' object has no attribute '%s'"
                                 % attr)

    def to_dict(self):
        return self.parse()

    def parse(self):
        """Return a representation of the Berksfile as a dict."""
        self.seek(0)
        data = utils.ruby_lines(self.readlines())
        data = [tuple(j.strip() for j in line.split(None, 1))
                for line in data]
        datamap = {}
        for line in data:
            if len(line) == 1:
                datamap[line[0]] = True
            elif len(line) == 2:
                key, value = line
                if key == 'cookbook':
                    datamap.setdefault('cookbook', {})
                    value = [utils.ruby_strip(v) for v in value.split(',')]
                    lib, detail = value[0], value[1:]
                    datamap['cookbook'].setdefault(lib, {})
                    # if there is additional dependency data but its
                    # not the ruby hash, its the version constraint
                    if detail and not any("".join(detail).startswith(o)
                                          for o in self.berks_options):
                        constraint, detail = detail[0], detail[1:]
                        datamap['cookbook'][lib]['constraint'] = constraint
                    if detail:
                        for deet in detail:
                            opt, val = [
                                utils.ruby_strip(i)
                                for i in deet.split(':', 1)
                            ]
                            if not any(opt == o for o in self.berks_options):
                                raise ValueError(
                                    "Cookbook detail '%s' does not specify "
                                    "one of '%s'" % (opt, self.berks_options))
                            else:
                                datamap['cookbook'][lib][opt.strip(':')] = (
                                    utils.ruby_strip(val))
                elif key == 'source':
                    datamap.setdefault(key, [])
                    datamap[key].append(utils.ruby_strip(value))
                elif key:
                    datamap[key] = utils.ruby_strip(value)
        self.seek(0)
        return datamap

    def merge(self, other):
        """Add requirements from 'other' Berksfile into this one."""
        if not isinstance(other, Berksfile):
            raise TypeError("Berksfile to merge should be a 'Berksfile' "
                            "instance, not %s.", type(other))
        current = self.to_dict()
        new = other.to_dict()

        berksfile_writelines = []
        # compare and gather cookbook dependencies
        for ckbkname, meta in new.get('cookbook', {}).items():
            if ckbkname in current.get('cookbook', {}):
                print '%s already has %s' % (self, ckbkname)
                continue
            line = "cookbook '%s'" % ckbkname
            if meta:
                # not like the others...
                if 'constraint' in meta:
                    line += ", '%s'" % meta.pop('constraint')
                for opt, spec in meta.iteritems():
                    line += ", %s: '%s'" % (opt, spec)
            berksfile_writelines.append("%s\n" % line)

        # compare and gather 'source' requirements
        for source in new.get('source', []):
            if source in current.get('source', []):
                continue
            line = "source '%s'" % source
            berksfile_writelines.append("%s\n" % line)
        return self.write_statements(berksfile_writelines)

    def write_statements(self, dependencies):
        """Insert new statements."""
        # TODO(sam): this is no longer Berksfile specific,
        # use this for writing Metadata.rb and others
        if not dependencies:
            return self.to_dict()
        assert isinstance(dependencies, list), "not a list"
        # ignore blanks
        dependencies = sorted([dep for dep in dependencies if dep])
        self.seek(0)
        orig_content = self.readlines()
        new_content = copy.copy(orig_content)

        # find all the insert points for each statement
        statements = {stmnt.split(None, 1)[0] for stmnt in dependencies}
        inserts = {}
        for line in reversed(orig_content):
            if not line:
                continue
            if not statements:
                break
            for statement in statements.copy():
                if line.startswith(statement):
                    index = orig_content.index(line) + 1
                    inserts[statement] = index
                    statements.remove(statement)

        for dep in dependencies:
            print "writing to Berksfile : %s" % dep
            startswith = dep.split(None, 1)[0]
            new_content.insert(
                inserts.get(startswith, len(new_content)), dep)

        if new_content != orig_content:
            self.seek(0)
            self.writelines(new_content)
        return self.to_dict()
