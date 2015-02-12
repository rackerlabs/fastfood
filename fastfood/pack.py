
import json
import os

from fastfood import utils


class TemplatePack(object):

    def __init__(self, path):
        """Initialize, asserting templatepack path and manifest."""
        self._manifest = None
        self._stencils = {}
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
    def stencils(self):
        return self._stencils

    def __getattr__(self, stencil_name):
        """Shortcut to self.load_stencil()."""
        return self.load_stencil(stencil_name)

    def load_stencil(self, stencil_name):
        """Return the Stencil from this template pack."""
        if stencil_name not in self._stencils:
            if stencil_name not in self.manifest['stencil_sets'].keys():
                raise AttributeError("Stencil set not listed in %s under "
                                     "stencil_sets." % self.manifest_path)
            stencil_path = os.path.join(
                self.path, 'stencils', stencil_name)
            try:
                self._stencils[stencil_name] = Stencil(stencil_path)
            except ValueError as err:
                raise AttributeError(err.message)
        return self._stencils[stencil_name]


class Stencil(object):

    def __init__(self, path):
        self.path = utils.normalize_path(path)
        if not os.path.isdir(path):
            raise ValueError("Stencil dir %s does not exist." % path)
        self.manifest_path = os.path.join(self.path, 'manifest.json')
        if not os.path.isfile(self.manifest_path):
            raise ValueError("Stencil needs manifest file, %s"
                             % self.manifest_path)
        self._manifest = None

    @property
    def manifest(self):
        if not self._manifest:
            with open(self.manifest_path) as man:
                self._manifest = json.load(man)
        return self._manifest

    def recipes(self):
        pass
