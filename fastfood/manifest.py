
import datetime
import errno
import logging
import os

from fastfood import book
from fastfood import pack
from fastfood import templating
from fastfood import utils

LOG = logging.getLogger(__name__)


def update_cookbook(cookbook_path, templatepack, stencilset_name, **options):

    tmppack = pack.TemplatePack(templatepack)
    cookbook = book.CookBook(cookbook_path)
    existing_deps = cookbook.metadata.get('depends', {}).keys()
    stencilset = tmppack.load_stencil_set(stencilset_name)

    if 'stencil' not in options:
        selected_stencil = stencilset.manifest.get('default_stencil')
    else:
        selected_stencil = options['stencil']
    if not selected_stencil:
        raise ValueError("No %s stencil specified." % stencilset_name)

    stencil = stencilset.get_stencil(selected_stencil, **options)

    stencil_deps = stencil.get('dependencies', {})

    # metadata dependencies
    metadata_writelines = []
    for lib, meta in stencil_deps.iteritems():
        if lib in existing_deps:
            continue
        elif meta and not isinstance(meta, list):
            raise TypeError("Stencil dependency metadata for %s in %s "
                            "should be an array of options, not %s."
                            % (lib, stencilset.manifest_path, type(meta)))
        else:
            line = "depends '%s'" % lib
            if meta:
                line = "%s '%s'" % (line, "', '".join(meta))
            metadata_writelines.append("%s\n" % line)

    # berks dependencies
    berksfile_writelines = []
    berksfile = cookbook.berksfile
    stencil_berks_deps = stencil.get('berks_dependencies', {})
    for lib, meta in stencil_berks_deps.iteritems():
        if lib in berksfile.get('cookbook', {}):
            continue
        elif meta and not isinstance(meta, dict):
            raise TypeError("Berksfile dependency hash for %s in %s "
                            "should be a dict of options, not %s."
                            % (lib, stencilset.manifest_path, type(meta)))
        else:
            line = "cookbook '%s'" % lib
            if meta:
                # not like the others...
                if 'constraint' in meta:
                    line += ", '%s'" % meta.pop('constraint')
                for opt, spec in meta.iteritems():
                    line += ", %s: '%s'" % (opt, spec)
            berksfile_writelines.append("%s\n" % line)

    # TODO: render files in stencil['files']
    # get recipe/test files?

    if metadata_writelines:
        cookbook.write_metadata_dependencies(
            metadata_writelines)

    if berksfile_writelines:
        cookbook.write_berksfile_dependencies(
            berksfile_writelines)


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
