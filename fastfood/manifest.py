
import json
import logging

import os
import sys

LOG = logging.getLogger(__name__)

def main(path):

    manifest = json.load(open(path))

    if 'api' not in manifest:
        raise ValueError("Manifest requires API version.")


    if 'stencil_sets' not in manifest:
        LOG.warning("No stencil_sets found in manifest.")
    print "manifest validated"


def gen(path):

    pass


if __name__ == '__main__':

    path = sys.argv[1]
    path = os.path.abspath(os.path.expanduser(os.path.normpath(path)))
    main(path)


