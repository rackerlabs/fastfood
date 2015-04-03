"""Functional tests for command line use."""

import errno
import os
import random
import shutil
import string
import tempfile
import unittest

from fastfood import pack
from fastfood import shell

TEST_TEMPLATEPACK = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 os.path.pardir, 'test_templatepack'))
assert os.path.isdir(TEST_TEMPLATEPACK), "Test templatepack not found."


class MockArgs(object):

    def __init__(self, **args):
        self._args = args
        for key, value in args.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        return repr(self._args)


class TestFastfoodCommands(unittest.TestCase):

    def setUp(self):

        self.templatepack_path = TEST_TEMPLATEPACK
        self.pack = pack.TemplatePack(self.templatepack_path)
        # make a separate ref in case something modifies the instance attr
        self.cookbooks_path = self._tmpcbd = tempfile.mkdtemp(
            prefix='%s.' % __file__, suffix='.cookbooks_dir')
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
        try:
            shutil.rmtree(self._tmpcbd)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise


class TestFastfoodNewCommand(TestFastfoodCommands):

    def test_fastfood_new(self):

        self.args.cookbook_name = ''.join(
            [random.choice(string.ascii_letters) for _ in xrange(10)])
        written, _ = shell._fastfood_new(self.args)
        # assert that files in pack manifest match the files
        # created by `fastfood new`
        base_path = '%s/' % os.path.join(
            self.cookbooks_path, self.args.cookbook_name)
        actual_files = [k[len(base_path):] for k in written
                        if k.startswith(base_path)]
        base_manifest_files = self.pack.manifest['base']['files']
        self.assertItemsEqual(actual_files, base_manifest_files)


if __name__ == '__main__':
    unittest.main()
