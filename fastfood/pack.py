
import json
import os

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
        """Shortcut to self.load_stencil()."""
        return self.load_stencil(stencilset_name)

    def load_stencil_set(self, stencilset_name):
        """Return the Stencil Set from this template pack."""
        if stencilset_name not in self._stencil_sets:
            if stencilset_name not in self.manifest['stencil_sets'].keys():
                raise AttributeError("Stencil set not listed in %s under "
                                     "stencil_sets." % self.manifest_path)
            stencil_path = os.path.join(
                self.path, 'stencils', stencilset_name)
            try:
                self._stencil_sets[stencilset_name] = StencilSet(stencil_path)
            except ValueError as err:
                raise AttributeError(err.message)
        return self._stencil_sets[stencilset_name]


class StencilSet(object):

    def __init__(self, path):
        self.path = utils.normalize_path(path)
        if not os.path.isdir(path):
            raise ValueError("Stencil Set dir %s does not exist." % path)
        self.manifest_path = os.path.join(self.path, 'manifest.json')
        if not os.path.isfile(self.manifest_path):
            raise ValueError("Stencil Set needs manifest file, %s"
                             % self.manifest_path)
        self._validate('api', cls=int)
        self._validate('default_stencil', cls=str)
        self._manifest = None
        self._stencils = {}

    def _validate(self, key, cls=None):
        if key not in self.manifest:
            raise ValueError("Stencil Set %s requires '%s'."
                             % (self.manifest_path, key))
        if cls:
            if not isinstance(self.manifest[key], cls):
                raise TypeError("Stencil Set value '%s' should be %s, not %s"
                                % (key, cls, type(self.manifest[key])))

    def _options(self, stencil):
        g_opts = self.manifest.get('options', {})
        if stencil in self._stencils:
            l_opts = self._stencils[stencil].get('options', {})
        else:
            raise ValueError("Stencil %s not a valid stencil" % stencil)

        return g_opts.update(l_opts)

    def load_stencils(self):
        if self.manifest.get('stencils'):
            self._stencils = self.manifest.get('stencils')
        return self._stencils

    @property
    def manifest(self):
        if not self._manifest:
            with open(self.manifest_path) as man:
                self._manifest = json.load(man)
        return self._manifest

    @property
    def stencils(self):
        return self._stencils

    def option_values(self, stencil, **o_map):
        opts = self._options(stencil)
        for opt in opts:
            if opt not in o_map:
                val = opt.get('default')
                if val:
                    o_map[opt] = val
                else:
                    o_map[opt] = ''

        return o_map
