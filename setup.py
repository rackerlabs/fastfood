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

import ast
import re
from setuptools import setup, find_packages


DEPENDENCIES = [
    'jinja2==2.7.3',
]
TESTS_REQUIRE = [
]


def package_meta():
    """Read __init__.py for global package metadata.

    Do this without importing the package.
    """
    _version_re = re.compile(r'__version__\s+=\s+(.*)')
    _url_re = re.compile(r'__url__\s+=\s+(.*)')
    _license_re = re.compile(r'__license__\s+=\s+(.*)')

    with open('fastfood/__init__.py', 'rb') as ffinit:
        initcontent = ffinit.read()
        version = str(ast.literal_eval(_version_re.search(
            initcontent.decode('utf-8')).group(1)))
        url = str(ast.literal_eval(_url_re.search(
            initcontent.decode('utf-8')).group(1)))
        licencia = str(ast.literal_eval(_license_re.search(
            initcontent.decode('utf-8')).group(1)))
    return {
        'version': version,
        'license': licencia,
        'url': url,
    }

_ff_meta = package_meta()


setup(
    name='fastfood',
    description='Chef Cookbook Wizardry',
    keywords='chef cookbook templates',
    version=_ff_meta['version'],
    tests_require=TESTS_REQUIRE,
    test_suite='tests',
    install_requires=DEPENDENCIES,
    packages=find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    license=_ff_meta['license'],
    maintainer='samstav',
    maintainer_email='smlstvnh@gmail.com',
    url=_ff_meta['url'],
    entry_points={
        'console_scripts': [
            'fastfood=fastfood.shell:main'
        ]
    },
)
