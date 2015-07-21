#!/usr/bin/env python

# Copyright 2015 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=invalid-name


"""Fastfood packaging and installation."""

import os
from setuptools import setup, find_packages

src_dir = os.path.dirname(os.path.realpath(__file__))

about = {}
with open(os.path.join(src_dir, 'fastfood', '__about__.py')) as abt:
    exec(abt.read(), about)


# README.rst is for fastfood's PyPI page
# pandoc --from=markdown_github --to=rst README.md --output=README.rst
with open(os.path.join(src_dir, 'README.rst')) as rdme:
    LONG_DESCRIPTION = rdme.read()


INSTALL_REQUIRES = [
    'Jinja2==2.7.3',
]


TESTS_REQUIRE = [
    'coverage==3.7.1',
    'flake8==2.4.1',
    'flake8-docstrings==0.2.1',
    'mock==1.2.0',
    'nose==1.3.7',
    'nose-ignore-docstring==0.2',
    'pylint==1.4.4',
    'vcrpy==1.6.1',
]


CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Topic :: Software Development',
    'Topic :: Software Development :: Code Generators',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
]


ENTRY_POINTS = {
    'console_scripts': ['fastfood=fastfood.shell:main'],
}


package_attributes = {
    'author': about['__author__'],
    'author_email': about['__email__'],
    'classifiers': CLASSIFIERS,
    'entry_points': ENTRY_POINTS,
    'name': about['__title__'],
    'description': about['__summary__'],
    'install_requires': INSTALL_REQUIRES,
    'keywords': ' '.join(about['__keywords__']),
    'license': about['__license__'],
    'long_description': LONG_DESCRIPTION,
    'packages': find_packages(exclude=['tests']),
    'test_suite': 'tests',
    'tests_require': TESTS_REQUIRE,
    'url': about['__url__'],
    'version': about['__version__'],
}


setup(**package_attributes)
