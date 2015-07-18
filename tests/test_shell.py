try:
    from StringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

import sys
import unittest

try:
    import mock
except ImportError:
    # Python 3
    import unittest.mock as mock

from vcrhelper import VCRHelper

import fastfood
from fastfood import shell

VERS_OUT = 'sys.stderr' if sys.version_info <= (3, 2, 0) else 'sys.stdout'


class TestFastfoodShell(VCRHelper):

    def test_pypi_release_info(self):
        with self.vcr.use_cassette('pypi_release_info.yaml'):
            info = shell._release_info()
            self.assertIn('releases', info)
            self.assertIn('urls', info)
            self.assertIn('info', info)

    @mock.patch('sys.stderr', new_callable=StringIO)
    @mock.patch('fastfood.__version__', new='0.1.6')
    def test_get_latest(self, mock_stderr):
        with self.vcr.use_cassette('pypi_release_info.yaml'):
            argv = ['--latest']
            with self.assertRaises(SystemExit):
                shell.main(argv=argv)
        mock_stderr.flush()
        mock_stderr.seek(0)
        output = mock_stderr.read()
        expected = (
            '%s  fastfood version 0.1.6 uploaded Thu Mar 26 19:24:55 2015\n'
            % shell.CHECK)
        self.assertEqual(output, expected)

    @mock.patch('sys.stderr', new_callable=StringIO)
    @mock.patch('fastfood.__version__', new='old')
    def test_get_latest_mock_old(self, mock_stderr):
        with self.vcr.use_cassette('pypi_release_info.yaml'):
            argv = ['--latest']
            with self.assertRaises(SystemExit):
                shell.main(argv=argv)
        mock_stderr.flush()
        mock_stderr.seek(0)
        output = mock_stderr.read()
        # prints EXCLAIM rather than CHECK
        expected = (
            '%s  fastfood version 0.1.6 uploaded Thu Mar 26 19:24:55 2015\n'
            % shell.EXCLAIM)
        self.assertEqual(output, expected)

    @mock.patch(VERS_OUT, new_callable=StringIO)
    def test_get_version(self, mock_output):
        argv = ['--version']
        with self.assertRaises(SystemExit):
            shell.main(argv=argv)
        mock_output.flush()
        mock_output.seek(0)
        output = mock_output.read()
        expected = 'fastfood version %s\n' % fastfood.__version__
        self.assertEqual(output, expected)

    @mock.patch(VERS_OUT, new_callable=StringIO)
    @mock.patch('fastfood.__version__', new='custom')
    def test_get_version_mocked(self, mock_output):
        argv = ['--version']
        with self.assertRaises(SystemExit):
            shell.main(argv=argv)

        mock_output.flush()
        mock_output.seek(0)
        output = mock_output.read()

        expected = 'fastfood version %s\n' % 'custom'
        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
