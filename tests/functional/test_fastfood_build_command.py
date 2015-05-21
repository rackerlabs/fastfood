"""Functional tests for command line use."""

import tempfile
import unittest
import os
from datetime import date

from fastfood import shell

import test_commands

BUILD_CONFIG = """
{
  "name": "test_build_cookbook",
  "stencils": [
    {
        "stencil_set": "base"
    },
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


class TestFastfoodBuildCommand(test_commands.TestFastfoodCommands):

    def test_fastfood_build_from_scratch(self):

        build_config_file = tempfile.NamedTemporaryFile()
        build_config_file.write(BUILD_CONFIG)
        build_config_file.seek(0)

        self.args.config_file = build_config_file.name
        _, cookbook = shell._fastfood_build(self.args)

        self.assertEqual(cookbook.name, 'test_build_cookbook')
        self.assertTrue(os.path.isdir(cookbook.path))

        metadata = cookbook.metadata.to_dict()

        # ensure name is passed from fastfood.json to cookbook name
        self.assertIn('test_build_cookbook', metadata['name'])
        self.assertIn('test_build_cookbook', cookbook.path)

        self.assertIn('sudo', metadata['depends'])
        self.assertIn('users', metadata['depends'])
        self.assertIn('rackops_rolebook', metadata['depends'])
        self.assertIn('nodejs', metadata['depends'])
        self.assertIn('newrelic', metadata['depends'])
        self.assertIn('rackspace_iptables', metadata['depends'])
        self.assertIn('ulimit', metadata['depends'])

        berks = cookbook.berksfile.to_dict()
        self.assertIn('nodejs', berks['cookbook'])

        # verify .kitchen.yml got the cookbook name correct
        kitchen_yml = os.path.join(cookbook.path, '.kitchen.yml')
        self.assertFileContains(kitchen_yml, 'test_build_cookbook::default')

        # it should also contain a partial template from the apache stencil
        self.assertFileContains(kitchen_yml, 'test_build_cookbook::_apache')

        default_rb = os.path.join(cookbook.path, 'recipes', 'default.rb')
        current_year = date.today().year
        self.assertFileContains(default_rb,
                                '# Cookbook Name:: test_build_cookbook')
        self.assertFileContains(default_rb,
                                ('# Copyright %s') % str(current_year))

        newrelic_rb = os.path.join(cookbook.path, 'recipes', 'newrelic.rb')
        self.assertTrue(os.path.isfile(newrelic_rb))

        # verify that multiple_stencils.txt was overwritten with last stencil
        # that appeared in ordered array in tests/functional/fastfood.json
        multiple_stencils_txt = os.path.join(cookbook.path,
                                             'multiple_stencils.txt')
        self.assertFileContains(multiple_stencils_txt, 'apache stencil')

if __name__ == '__main__':
    unittest.main()
