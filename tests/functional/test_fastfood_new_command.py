"""Functional tests for command line use."""

import os
import random
import string
import unittest

from fastfood import shell

import test_commands


class TestFastfoodNewCommand(test_commands.TestFastfoodCommands):

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
