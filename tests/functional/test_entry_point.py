"""Functional tests for command line use."""

import subprocess
import unittest


class TestFastfoodCLI(unittest.TestCase):

    def test_fastfood_command_is_there(self):

        cmd = ['fastfood', '--help']
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, OSError) as err:
            msg = 'Error while running `%s`' % subprocess.list2cmdline(cmd)
            self.fail(msg='%s --> %r' % (msg, err))

    def test_help_output(self):
        cmd = ['fastfood', '--help']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, OSError) as err:
            msg = 'Error while running `%s`' % subprocess.list2cmdline(cmd)
            self.fail(msg='%s --> %r' % (msg, err))
        self.assertIn('usage', output.lower())


if __name__ == '__main__':
    unittest.main()
