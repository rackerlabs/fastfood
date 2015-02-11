
import datetime
import errno
import json
import logging
import os

from fastfood import templating
from fastfood import utils

LOG = logging.getLogger(__name__)


def create_new_cookbook(cookbook_name, templatepack, target, force_new=False):
    """Create a new cookbook.

    :param cookbook_name: Name of the new cookbook.
    :param templatepack: Path to templatepack.
    :param target: Target dir for new cookbook.
    """
    templatepack = utils.normalize_path(templatepack)
    target = utils.normalize_path(target)

    if not os.path.exists(templatepack):
        raise ValueError("Templatepack at %s does not exist."
                         % os.path.relpath(templatepack))
    tpmanifest_path = os.path.join(templatepack, 'manifest.json')
    if not os.path.isfile(tpmanifest_path):
        raise ValueError("Templatepack needs manifest file, %s"
                         % os.path.relpath(tpmanifest_path))

    tpmanifest = json.load(open(tpmanifest_path))
    if 'api' not in tpmanifest:
        raise ValueError("Manifest %s requires 'api' specifying version."
                         % os.path.relpath(tpmanifest_path))

    if 'base' not in tpmanifest:
        raise ValueError("No 'base' content for new cookbook found in %s"
                         % os.path.relpath(tpmanifest_path))
    elif not isinstance(tpmanifest, dict):
        raise TypeError("'base' content should be an object.")

    files, directories = [], []
    for option, data in tpmanifest['base'].iteritems():
        if option == 'files':
            if not isinstance(data, list):
                raise TypeError("Base files should be a list of files.")
            files = data
        elif option == 'directories':
            if not isinstance(data, list):
                raise TypeError("Base directories should be a list of "
                                "directory names.")
            directories = data
        else:
            raise ValueError("Unknown 'base' option '%s'" % option)

    if files:
        if not os.path.exists(target):
            raise ValueError("Target cookbook dir %s does not exist."
                             % os.path.relpath(target))

    template_map = {
        'cookbook': {
            'name': cookbook_name,
            'year': datetime.datetime.now().year,
            }
        }

    template_files = [os.path.join(templatepack, 'base', f)
                      for f in files]
    path_map = dict(zip(template_files, files))
    filetable = templating.render_templates(*template_files, **template_map)

    for path in directories:
        target_dir = os.path.join(target, cookbook_name, path)
        LOG.debug("Creating dir -> %s", target_dir)
        os.makedirs(target_dir)

    for orig_path, content in filetable:
        target_path = os.path.join(
            target, cookbook_name, path_map[orig_path])
        needdir = os.path.dirname(target_path)
        assert needdir, "Target should have valid parent dir"
        try:
            os.makedirs(needdir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        if os.path.isfile(target_path):
            if force_new:
                LOG.warning("Forcing overwrite of existing file %s.",
                            target_path)
            else:
                LOG.info("Skipping existing file %s", target_path)
                continue
        else:
            with open(target_path, 'w') as newfile:
                LOG.info("Writing rendered file %s", target_path)
                newfile.write(content)
