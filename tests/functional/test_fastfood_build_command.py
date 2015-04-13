"""Functional tests for command line use."""

import tempfile
import unittest

from fastfood import shell

import test_commands

BUILD_CONFIG = """
{
  "name": "test_build_cookbook",
  "stencils": [
    {
      "stencil_set": "utility",
      "stencil": "default",
      "openfor": "test_build_cookbook"
    },
    {
      "stencil_set": "nodejs"
    },
    {
      "stencil_set": "newrelic"
    },
    {
      "stencil_set": "apache"
    }
  ]
}
""".strip()


class TestFastfoodNewCommand(test_commands.TestFastfoodCommands):

    def test_fastfood_build_from_scratch(self):

        build_config_file = tempfile.NamedTemporaryFile()
        build_config_file.write(BUILD_CONFIG)
        build_config_file.seek(0)

        self.args.config_file = build_config_file.name
        _, cookbook = shell._fastfood_build(self.args)
        self.assertEqual(cookbook.name, 'test_build_cookbook')
        metadata = cookbook.metadata.to_dict()
        self.assertIn('sudo', metadata['depends'])
        self.assertIn('users', metadata['depends'])
        self.assertIn('rackops_rolebook', metadata['depends'])
        self.assertIn('nodejs', metadata['depends'])
        self.assertIn('newrelic', metadata['depends'])
        self.assertIn('rackspace_iptables', metadata['depends'])
        self.assertIn('ulimit', metadata['depends'])
        berks = cookbook.berksfile.to_dict()
        self.assertIn('nodejs', berks['cookbook'])

if __name__ == '__main__':
    unittest.main()
