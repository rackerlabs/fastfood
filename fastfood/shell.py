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

"""Fastfood - cookbook wizardry.

CLI Module
"""

from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import sys
import threading

from fastfood import food

_local = threading.local()
LOG = logging.getLogger(__name__)
NAMESPACE = 'fastfood'


def _fastfood_gen(args):

    return food.update_cookbook(
        args.cookbook, args.template_pack, args.stencil_set,
        force=args.force, **args.options)


def _fastfood_new(args):
    return food.create_new_cookbook(
        args.cookbook_name, args.template_pack, args.cookbooks)


def _fastfood_build(args):

    return food.build_cookbook(
        args.config_file, args.template_pack,
        args.cookbooks, cookbook_path=args.cookbook)


def _split_key_val(option):
    key_val = option.split(':', 1)
    assert len(key_val) == 2, "Bad option %s" % option
    return key_val


def getenv(option_name, default=None):
    env = "%s_%s" % (NAMESPACE.upper(), option_name.upper())
    return os.environ.get(env, default)


def main():
    """fastfood command line interface."""
    import argparse
    import traceback

    class HelpfulParser(argparse.ArgumentParser):
        def error(self, message, print_help=False):
            if 'too few arguments' in message:
                sys.argv.insert(0, os.path.basename(sys.argv.pop(0)))
                message = ("%s. Try getting help with `%s -h`"
                           % (message, " ".join(sys.argv)))
            if print_help:
                self.print_help()
            sys.stderr.write('\nerror: %s\n' % message)
            sys.exit(2)

    parser = HelpfulParser(
        description=__doc__.splitlines()[0],
        epilog="\n".join(__doc__.splitlines()[1:]),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument('-v', dest='loglevel', action='store_const',
                         const=logging.INFO,
                         help="Set log-level to INFO.")
    verbose.add_argument('-vv', dest='loglevel', action='store_const',
                         const=logging.DEBUG,
                         help="Set log-level to DEBUG.")
    parser.set_defaults(loglevel=logging.WARNING)
    parser.add_argument(
        '--template-pack', help='template pack location',
        default=getenv(
            'template_pack', os.path.join(os.getenv('HOME'), '.fastfood')))
    parser.add_argument(
        '--cookbooks', help='cookbooks directory',
        default=getenv(
            'cookbooks', os.path.join(os.getenv('HOME'), 'cookbooks')))

    subparsers = parser.add_subparsers(
        dest='_subparsers', title='fastfood commands',
        description='operations...',
        help='...')
    #
    # `fastfood gen`
    #
    gen_parser = subparsers.add_parser(
        'gen', help='Create a new recipe for an existing cookbook.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    gen_parser.add_argument('stencil_set',
                            help="Stencil set to use.")
    gen_parser.add_argument('options', nargs='*', type=_split_key_val,
                            metavar='option',
                            help="Stencil options.")
    gen_parser.add_argument(
        '-c', '--cookbook', default=os.getcwd(),
        help="Target cookbook. (defaults to current working directory)")
    gen_parser.add_argument('--force', '-f', action='store_true',
                            default=False, help="Overwrite existing files.")
    gen_parser.set_defaults(func=_fastfood_gen)

    #
    # `fastfood new`
    #
    new_parser = subparsers.add_parser(
        'new', help='Create a cookbook.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    new_parser.add_argument('cookbook_name',
                            help="Name of the new cookbook.")
    new_parser.set_defaults(func=_fastfood_new)

    #
    # `fastfood build`
    #
    build_parser = subparsers.add_parser(
        'build', help='Create or update a cookbook using a config',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    build_parser.add_argument('config_file',
                              help="JSON config file")
    build_parser.add_argument(
        '-c', '--cookbook', default=os.getcwd(),
        help="Target cookbook (optional).")
    build_parser.set_defaults(func=_fastfood_build)

    setattr(_local, 'argparser', parser)
    args = parser.parse_args()
    if hasattr(args, 'options'):
        args.options = {k: v for k, v in args.options}

    logging.basicConfig(level=args.loglevel)

    try:
        print(args.func(args))
    except Exception as err:
        traceback.print_exc()
        # todo: tracack in -v or -vv mode?
        sys.stderr.write("%s\n" % repr(err))
        sys.stderr.flush()
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit("\nStahp")
    else:
        print('success')
        # result

if __name__ == '__main__':
    main()
