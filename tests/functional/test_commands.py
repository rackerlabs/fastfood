"""Functional tests for command line use."""

import errno
import os
import shutil
import tempfile
import unittest

from fastfood import pack

TEST_TEMPLATEPACK = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 os.path.pardir, 'test_templatepack'))
assert os.path.isdir(TEST_TEMPLATEPACK), "Test templatepack not found."


class MockArgs(object):

    def __init__(self, **args):
        self.__dict__['_args'] = args

    def __setattr__(self, key, val):
        self._args[key] = val

    def __getattr__(self, attr):
        return self._args[attr]

    def __repr__(self):
        return '<MockArgs %s>' % repr(self._args)


class TestFastfoodCommands(unittest.TestCase):

    def create_tempdir(self, **kw):
        kw.setdefault('prefix', '%s-' % __file__)
        new = tempfile.mkdtemp(**kw)
        self.tempdirs.append(new)
        return new

    def setUp(self):

        self.tempdirs = []
        self.templatepack_path = TEST_TEMPLATEPACK
        self.pack = pack.TemplatePack(self.templatepack_path)
        # make a separate ref in case something modifies the instance attr
        self.cookbooks_path = self._tmpcbd = self.create_tempdir(
            suffix='.cookbooks_dir')

        cli_args = {
            'template_pack': self.templatepack_path,
            'cookbooks': self.cookbooks_path,
            'cookbook': None,
            'cookbook_name': None,
            'force': None,
            'options': None,  # stencil options
            'config_file': None,  # for `fastfood build`
        }
        self.args = MockArgs(**cli_args)

    def tearDown(self):
        for tmpd in self.tempdirs:
            try:
                shutil.rmtree(tmpd)
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise


if __name__ == '__main__':
    unittest.main()
