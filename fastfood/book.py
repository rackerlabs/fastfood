
import copy
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
            self._metadata = self._parse_metadata()
        return self._metadata

    @property
    def berksfile(self):
        """Return dict representation of this cookbook's Berksfile."""
        if not self._berksfile:
            if not os.path.isfile(self.berks_path):
                raise ValueError("No Berksfile found at %s"
                                 % self.berks_path)
            self._berksfile = self._parse_berksfile()
        return self._berksfile

    def _parse_berksfile(self):
        assert os.path.isfile(self.berks_path), "Berksfile not found"
        # allowed options
        #   - branch
        #   - git
        #   - path
        #   - ref
        #   - revision
        #   - tag
        #

    # see https://github.com/the-galley/chef-templatepack/blob/master/base/Berksfile

    def _parse_metadata(self):
        """Open metadata.rb and generate useful map."""
        assert os.path.isfile(self.metadata_path), "metadata.rb not found"
        with open(self.metadata_path) as meta:
            data = meta.readlines()
        # honors pound sign comments but not ruby block comments
        data = [l.replace('\t', ' ') for l in data if l.strip()
                and not l.strip().startswith('#')]
        data = [tuple(j.strip() for j in line.split(None, 1))
                for line in data]
        depends = {}
        for key, value in data:
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
                new_content.insert(where, dep)
            # uniq
            new_content = list(set(new_content))
            if new_content != orig_content:
                meta.seek(0)
                meta.writelines(new_content)
        # reset self.metadata property
        self._metadata = None
        return self.metadata
