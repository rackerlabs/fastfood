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

"""Fastfood Template Pack manager."""

import json
import os

from fastfood import stencil as stencil_module
from fastfood import utils


class TemplatePack(object):

    def __init__(self, path):
        """Initialize, asserting templatepack path and manifest."""
        self._manifest = None
        self._stencil_sets = {}
        self.path = utils.normalize_path(path)
        if not os.path.isdir(path):
            raise ValueError("Templatepack dir %s does not exist."
                             % self.path)
        self.manifest_path = os.path.join(self.path, 'manifest.json')
        if not os.path.isfile(self.manifest_path):
            raise ValueError("Templatepack needs manifest file, %s"
                             % os.path.relpath(self.manifest_path))
        self._validate('api', cls=int)
        self._validate('base', cls=dict)
        # for caching Stencil instances

    def _validate(self, key, cls=None):
        if key not in self.manifest:
            raise ValueError("Manifest %s requires '%s'."
                             % (self.manifest_path, key))
        if cls:
            if not isinstance(self.manifest[key], cls):
                raise TypeError("Manifest value '%s' should be %s, not %s"
                                % (key, cls, type(self.manifest[key])))

    @property
    def manifest(self):
        if not self._manifest:
            with open(self.manifest_path) as man:
                self._manifest = json.load(man)
        return self._manifest

    @property
    def stencil_sets(self):
        return self._stencil_sets

    def __getattr__(self, stencilset_name):
        """Shortcut to self.load_stencil_set()."""
        return self.load_stencil_set(stencilset_name)

    def load_stencil_set(self, stencilset_name):
        """Return the Stencil Set from this template pack."""
        if stencilset_name not in self._stencil_sets:
            if stencilset_name not in self.manifest['stencil_sets'].keys():
                raise AttributeError("Stencil set '%s' not listed in %s under "
                                     "stencil_sets."
                                     % (stencilset_name, self.manifest_path))
            stencil_path = os.path.join(
                self.path, 'stencils', stencilset_name)
            try:
                self._stencil_sets[stencilset_name] = (
                    stencil_module.StencilSet(stencil_path))
            except ValueError as err:
                raise AttributeError(err.message)
        return self._stencil_sets[stencilset_name]
