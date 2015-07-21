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

    """Chef Cookbook object.

    Understands metadata.rb, Berksfile and how to parse them.
    """

    def __init__(self, path):
        """Initialize CookBook wrapper at 'path'."""
        self.path = utils.normalize_path(path)
        self._metadata = None
        if not os.path.isdir(path):
            raise ValueError("Cookbook dir %s does not exist."
                             % self.path)
        self._berksfile = None

    @property
    def name(self):
        """Cookbook name property."""
        try:
            return self.metadata.to_dict()['name']
        except KeyError:
            raise LookupError("%s is missing 'name' attribute'."
                              % self.metadata)

    @property
    def metadata(self):
        """Return dict representation of this cookbook's metadata.rb ."""
        self.metadata_path = os.path.join(self.path, 'metadata.rb')
        if not os.path.isfile(self.metadata_path):
            raise ValueError("Cookbook needs metadata.rb, %s"
                             % self.metadata_path)

        if not self._metadata:
            self._metadata = MetadataRb(open(self.metadata_path, 'r+'))

        return self._metadata

    @property
    def berksfile(self):
        """Return this cookbook's Berksfile instance."""
        self.berks_path = os.path.join(self.path, 'Berksfile')
        if not self._berksfile:
            if not os.path.isfile(self.berks_path):
                raise ValueError("No Berksfile found at %s"
                                 % self.berks_path)
            self._berksfile = Berksfile(open(self.berks_path, 'r+'))
        return self._berksfile


class MetadataRb(utils.FileWrapper):

    """Wrapper for a metadata.rb file."""

    @classmethod
    def from_dict(cls, dictionary):
        """Create a MetadataRb instance from a dict."""
        cookbooks = set()
        # put these in order
        groups = [cookbooks]

        for key, val in dictionary.items():
            if key == 'depends':
                cookbooks.update({cls.depends_statement(cbn, meta)
                                  for cbn, meta in val.items()})

        body = ''
        for group in groups:
            if group:
                body += '\n'
            body += '\n'.join(group)
        return cls.from_string(body)

    @staticmethod
    def depends_statement(cookbook_name, metadata=None):
        """Return a valid Ruby 'depends' statement for the metadata.rb file."""
        line = "depends '%s'" % cookbook_name
        if metadata:
            if not isinstance(metadata, dict):
                raise TypeError("Stencil dependency options for %s "
                                "should be a dict of options, not %s."
                                % (cookbook_name, metadata))
            if metadata:
                line = "%s '%s'" % (line, "', '".join(metadata))
        return line

    def to_dict(self):
        """Return a dictionary representation of this metadata.rb file."""
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

    def merge(self, other):
        """Add requirements from 'other' metadata.rb into this one."""
        if not isinstance(other, MetadataRb):
            raise TypeError("MetadataRb to merge should be a 'MetadataRb' "
                            "instance, not %s.", type(other))
        current = self.to_dict()
        new = other.to_dict()

        # compare and gather cookbook dependencies
        meta_writelines = ['%s\n' % self.depends_statement(cbn, meta)
                           for cbn, meta in new.get('depends', {}).items()
                           if cbn not in current.get('depends', {})]

        self.write_statements(meta_writelines)
        return self.to_dict()


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
        """Return a dictionary representation of this Berksfile."""
        return self.parse()

    def parse(self):
        """Parse this Berksfile into a dict."""
        self.flush()
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

    @classmethod
    def from_dict(cls, dictionary):
        """Create a Berksfile instance from a dict."""
        cookbooks = set()
        sources = set()
        other = set()
        # put these in order
        groups = [sources, cookbooks, other]

        for key, val in dictionary.items():
            if key == 'cookbook':
                cookbooks.update({cls.cookbook_statement(cbn, meta)
                                  for cbn, meta in val.items()})
            elif key == 'source':
                sources.update({"source '%s'" % src for src in val})
            elif key == 'metadata':
                other.add('metadata')

        body = ''
        for group in groups:
            if group:
                body += '\n'
            body += '\n'.join(group)
        return cls.from_string(body)

    @staticmethod
    def cookbook_statement(cookbook_name, metadata=None):
        """Return a valid Ruby 'cookbook' statement for the Berksfile."""
        line = "cookbook '%s'" % cookbook_name
        if metadata:
            if not isinstance(metadata, dict):
                raise TypeError("Berksfile dependency hash for %s "
                                "should be a dict of options, not %s."
                                % (cookbook_name, metadata))
            # not like the others...
            if 'constraint' in metadata:
                line += ", '%s'" % metadata.pop('constraint')
            for opt, spec in metadata.items():
                line += ", %s: '%s'" % (opt, spec)
        return line

    def merge(self, other):
        """Add requirements from 'other' Berksfile into this one."""
        if not isinstance(other, Berksfile):
            raise TypeError("Berksfile to merge should be a 'Berksfile' "
                            "instance, not %s.", type(other))
        current = self.to_dict()
        new = other.to_dict()

        # compare and gather cookbook dependencies
        berks_writelines = ['%s\n' % self.cookbook_statement(cbn, meta)
                            for cbn, meta in new.get('cookbook', {}).items()
                            if cbn not in current.get('cookbook', {})]

        # compare and gather 'source' requirements
        berks_writelines.extend(["source '%s'\n" % src for src
                                 in new.get('source', [])
                                 if src not in current.get('source', [])])

        self.write_statements(berks_writelines)
        return self.to_dict()
