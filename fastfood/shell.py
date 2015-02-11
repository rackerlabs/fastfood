# -*- coding: utf-8 -*-
"""fastfood - cookbook wizardry"""
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os
import sys
import threading

from fastfood import manifest

_local = threading.local()
LOG = logging.getLogger(__name__)
NAMESPACE = 'fastfood'


def _fastfood_gen(args):
    print(args)


def _fastfood_new(args):
    cookbook_name = args.cookbook_name
    templatepack = args.template_pack
    cookbooks = args.cookbook_path
    return manifest.create_new_cookbook(
        cookbook_name, templatepack, cookbooks)


def _fastfood_build(args):
    print(args)


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
    parser.add_argument('--template-pack', help='template pack location', metavar='template_pack',
                        default=getenv('template_pack', os.path.join(os.getenv('HOME'), '.fastfood')))
    parser.add_argument('--cookbook-path', help='cookbooks directory', metavar='cookbook_path',
                        default=getenv('cookbook_path', os.path.join(os.getenv('HOME'), 'cookbooks')))

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
    gen_parser.add_argument('--force, -f', action='store_true', default=False,
                            help="Overwrite existing files.")
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
    build_parser.set_defaults(func=_fastfood_build)


    setattr(_local, 'argparser', parser)
    args = parser.parse_args()
    if getattr(args, 'options', None):
        args.options = {k:v for k,v in args.options}

    try:
        result = args.func(args)
    except Exception as err:
        traceback.print_exc()
        # todo: tracack in -v or -vv mode?
        sys.stderr.write("%s\n" % repr(err))
        sys.stderr.flush()
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit("\nStahp")
    else:
        import ipdb;ipdb.set_trace()
        # result

if __name__ == '__main__':
    main()
