
import collections
import datetime
import errno
import logging
import os

from fastfood import book
from fastfood import pack
from fastfood import templating
from fastfood import utils

LOG = logging.getLogger(__name__)


def update_cookbook(cookbook_path, templatepack, stencilset, **options):

    tmppack = pack.TemplatePack(templatepack)
    cookbook = book.CookBook(cookbook_path)
    existing_deps = cookbook.metadata.get('depends', {}).keys()
    stencil = tmppack.load_stencil(stencilset)
    stencil_deps = stencil.manifest.get('dependencies', {})
    writelines = collections.deque()
    for lib, meta in stencil_deps.iteritems():
        if lib in existing_deps:
            continue
        elif meta and not isinstance(meta, list):
            raise TypeError("Stencil dependency metadata for %s in %s "
                            "should be an array of options, not %s."
                            % (lib, stencil.manifest_path, type(meta)))
        elif meta:
            line = "depends '%s'" % "', '".join(meta)
            writelines.append(line)
        else:
            writelines.append("depends '%s'" % lib)
    if writelines:
        updated_meta = cookbook.write_metadata_dependencies(writelines)

    import ipdb;ipdb.set_trace()


def create_new_cookbook(cookbook_name, templatepack,
                        target, force_new=False):
    """Create a new cookbook.

    :param cookbook_name: Name of the new cookbook.
    :param templatepack: Path to templatepack.
    :param target: Target dir for new cookbook.

    TODO:
        return something, like files added or path to new cookbook or both
    """
    target = utils.normalize_path(target)

    tmppack = pack.TemplatePack(templatepack)
    tpmanifest = tmppack.manifest

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
        try:
            os.makedirs(target_dir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
            else:
                LOG.info("Skipping existing directory %s",
                         target_dir)

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
