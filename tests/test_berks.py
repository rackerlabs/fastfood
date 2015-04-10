"""Berksfile related tests."""

import unittest

FIRST_BERKS = """
source 'https://supermarket.getchef.com'

cookbook 'newrelic_plugins', git: 'git@github.com:rackspace-cookbooks/newrelic_plugins_chef.git'
cookbook 'disable_ipv6', path: 'test/fixtures/cookbooks/disable_ipv6'
cookbook 'wrapper', path: 'test/fixtures/cookbooks/wrapper'
cookbook 'apt'

# until https://github.com/elasticsearch/cookbook-elasticsearch/pull/230
cookbook 'elasticsearch', '~> 0.3', git:'git@github.com:racker/cookbook-elasticsearch.git'

# until https://github.com/lusis/chef-logstash/pull/336 & 394
cookbook 'logstash', git:'git@github.com:racker/chef-logstash.git'

metadata
"""

SECOND_BERKS = """
source "https://supermarket.chef.io"

metadata

cookbook 'cron', git: 'git@github.com:rackspace-cookbooks/cron.git'
# until https://github.com/elastic/cookbook-elasticsearch/pull/230

cookbook 'disable_ipv6', path: 'test/fixtures/cookbooks/disable_ipv6'
cookbook 'wrapper', path: 'test/fixtures/cookbooks/wrapper'
cookbook 'yum'

cookbook 'fake', '~> 9.1'
"""

import copy

from fastfood import book

class TestBerks(unittest.TestCase):

    def test_merge(self):

        fb = book.Berksfile.from_string(FIRST_BERKS)
        before = copy.deepcopy(fb.to_dict())
        self.assertIn('cookbook', before)
        self.assertIsInstance(before['cookbook'], dict)
        self.assertNotIn('cron', before['cookbook'])
        self.assertNotIn('fake', before['cookbook'])
        self.assertNotIn('yum', before['cookbook'])
        self.assertIn('source', before)
        self.assertIsInstance(before['source'], list)
        self.assertNotIn('https://supermarket.chef.io', before['source'])

        sb = book.Berksfile.from_string(SECOND_BERKS)
        fb.merge(sb)
        after = fb.to_dict()

        self.assertIn('cron', after['cookbook'])
        self.assertIn('fake', after['cookbook'])
        self.assertIn('yum', after['cookbook'])
        self.assertIn('source', after)
        self.assertEqual(after['source'],
                ['https://supermarket.getchef.com',
                 'https://supermarket.chef.io'])
        self.assertEqual(after['cookbook']['fake']['constraint'],
                        '~> 9.1')
        self.assertEqual(after['cookbook']['cron']['git'],
                         'git@github.com:rackspace-cookbooks/cron.git')

    def test_berks_to_dict(self):

        fb = book.Berksfile.from_string(FIRST_BERKS)
        self.assertIsInstance(fb, book.Berksfile)
        fbd = fb.to_dict()
        self.assertIsInstance(fbd, dict)
        self.assertIn('cookbook', fbd)
        self.assertIsInstance(fbd['cookbook'], dict)
        self.assertIn('source', fbd)
        self.assertIsInstance(fbd['source'], list)
        self.assertIn('https://supermarket.getchef.com', fbd['source'])
        self.assertIn('metadata', fbd)
        self.assertTrue(fbd['metadata'] is True)

        expects = [
            'newrelic_plugins',
            'disable_ipv6',
            'elasticsearch',
            'wrapper',
            'apt',
            'logstash',
        ]
        self.assertEqual(len(fbd['cookbook']), len(expects))
        for cb in expects:
            self.assertIn(cb, fbd['cookbook'])

        self.assertEqual(
            fbd['cookbook']['newrelic_plugins']['git'],
            'git@github.com:rackspace-cookbooks/newrelic_plugins_chef.git')
        self.assertEqual(
            fbd['cookbook']['disable_ipv6']['path'],
            'test/fixtures/cookbooks/disable_ipv6')
        self.assertEqual(
            fbd['cookbook']['wrapper']['path'],
            'test/fixtures/cookbooks/wrapper')
        self.assertEqual(fbd['cookbook']['apt'], {})
        self.assertEqual(
            fbd['cookbook']['elasticsearch']['constraint'],
            '~> 0.3')
        self.assertEqual(
            fbd['cookbook']['elasticsearch']['git'],
            'git@github.com:racker/cookbook-elasticsearch.git')
        self.assertEqual(
            fbd['cookbook']['logstash']['git'],
            'git@github.com:racker/chef-logstash.git')


if __name__ == '__main__':
    unittest.main()
