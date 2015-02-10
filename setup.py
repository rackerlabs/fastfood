import re
import ast
from setuptools import setup, find_packages


#_version_re = re.compile(r'__version__\s+=\s+(.*)')
#_url_re = re.compile(r'__url__\s+=\s+(.*)')


#with open('fastfood/__init__.py', 'rb') as f:
#    f = f.read()
#    version = str(ast.literal_eval(_version_re.search(
#        f.decode('utf-8')).group(1)))
#    url = str(ast.literal_eval(_url_re.search(
#        f.decode('utf-8')).group(1)))


dependencies = [
]
tests_require = [
    'mock',
]

setup(
    name='fastfood',
    description='...',
    keywords='...',
    version='1.0',
    url='https://github.com/rackerlabs/fastfood',
    tests_require=tests_require,
    test_suite='tests',
    install_requires=dependencies,
    packages=find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    license='Apache License (2.0)',
    entry_points={
        'console_scripts': [
            'fastfood=fastfood.shell:main'
        ]
    },
)
