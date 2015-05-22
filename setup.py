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

"""Fastfood packaging and installation."""

import os
from setuptools import setup, find_packages

DEPENDENCIES = [
    'jinja2==2.7.3',
]
TESTS_REQUIRE = [
]

src_dir = os.path.dirname(os.path.realpath(__file__))

about = {}
with open(os.path.join(src_dir, 'fastfood', '__about__.py')) as abt:
    exec(abt.read(), about)


setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__summary__'],
    license=about['__license__'],
    url=about['__url__'],
    author=about['__author__'],
    maintainer_email=about['__email__'],
    keywords='chef cookbook templates',
    tests_require=TESTS_REQUIRE,
    test_suite='tests',
    install_requires=DEPENDENCIES,
    packages=find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    entry_points={
        'console_scripts': [
            'fastfood=fastfood.shell:main'
        ]
    },
)
