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
#
# pylint: disable=invalid-name

"""Fastfood Stencil Set manager."""

import copy
import json
import os

from fastfood import exc
from fastfood import utils

# python 2 vs. 3 string types
try:
    basestring
except NameError:
    basestring = str


class StencilSet(object):

    """The stencil set object.

    Holds references to stencils in the set.
    """

    def __init__(self, path):
        """Initialize the stencilset object with a local path."""
        # assign these attrs early
        self._manifest = None
        self._stencils = {}

        self.path = utils.normalize_path(path)
        if not os.path.isdir(path):
            raise exc.FastfoodStencilSetInvalidPath(
                "Stencil Set dir %s does not exist." % path)
        self.manifest_path = os.path.join(self.path, 'manifest.json')
        if not os.path.isfile(self.manifest_path):
            raise exc.FastfoodStencilSetMissingManifest(
                "Stencil Set needs manifest file, %s"
                % self.manifest_path)
        self._validate('api', cls=int)
        self._validate('default_stencil', cls=basestring)

    def _validate(self, key, cls=None):
        """Verify the manifest schema."""
        if key not in self.manifest:
            raise ValueError("Stencil Set %s requires '%s'."
                             % (self.manifest_path, key))
        if cls:
            if not isinstance(self.manifest[key], cls):
                raise TypeError("Stencil Set value '%s' should be %s, not %s"
                                % (key, cls, type(self.manifest[key])))

    @property
    def manifest(self):
        """The manifest definition of the stencilset as a dict."""
        if not self._manifest:
            with open(self.manifest_path) as man:
                self._manifest = json.load(man)
        return self._manifest

    @property
    def stencils(self):
        """List of stencils."""
        if not self._stencils:
            self._stencils = self.manifest['stencils']
        return self._stencils

    def get_stencil(self, stencil_name, **options):
        """Return a Stencil instance given a stencil name."""
        if stencil_name not in self.manifest.get('stencils', {}):
            raise ValueError("Stencil '%s' not declared in StencilSet "
                             "manifest." % stencil_name)
        stencil = copy.deepcopy(self.manifest)
        allstencils = stencil.pop('stencils')
        stencil.pop('default_stencil', None)
        override = allstencils[stencil_name]
        utils.deepupdate(stencil, override)

        # merge options, prefer **options (probably user-supplied)
        for opt, data in stencil.get('options', {}).items():
            if opt not in options:
                options[opt] = data.get('default', '')
        stencil['options'] = options

        name = stencil['options'].get('name')
        files = stencil['files'].copy()
        for fil, templ in files.items():
            if '<NAME>' in fil:
                # check for the option b/c there are
                # cases in which it may not exist
                if not name:
                    raise ValueError("Stencil does not include a name option")

                stencil['files'].pop(fil)
                fil = fil.replace('<NAME>', name)
                stencil['files'][fil] = templ

        return stencil
