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
from __future__ import print_function

import os

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
            with open(self.metadata_path) as meta:
                self._metadata = MetadataRb(meta)
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


class MetadataRb(utils.FileWrapper):

    """Wrapper for a metadata.rb file."""

    def to_dict(self):
        return self.parse()

    def parse(self):
        """Parse the metadata.rb into a dict."""
        data = utils.ruby_lines(self.readlines())
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
        datamap = {key: utils.ruby_strip(val) for key, val in data}
        if depends:
            datamap['depends'] = depends
        self.seek(0)
        return datamap


class Berksfile(utils.FileWrapper):

    """Wrapper for a Berksfile."""

    berks_options = [
        'branch',
        'git',
        'path',
        'ref',
        'revision',
        'tag',
    ]

    def to_dict(self):
        return self.parse()

    def parse(self):
        """Parse this Berksfile into a dict."""
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
        berks_writelines.extend(["source '%s'\n" % src for src
                                 in new.get('source', [])
                                 if src not in current.get('source', [])])

        self.write_statements(berks_writelines)
        return self.to_dict()
