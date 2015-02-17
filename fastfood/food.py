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

"""Fastfood core module."""

from __future__ import print_function
from __future__ import unicode_literals

import datetime
import errno
import json
import logging
import os

from fastfood import book
from fastfood import pack
from fastfood import templating
from fastfood import utils

LOG = logging.getLogger(__name__)


def build_cookbook(build_config, templatepack, cookbooks_home,
                   cookbook_path=None, force=False):

    with open(build_config) as cfg:
        cfg = json.load(cfg)

    cookbook = None
    if cookbook_path:
        try:
            cookbook = book.CookBook(cookbook_path)
        # change this to a more specific error
        except ValueError:
            # create a new one please
            pass

    if not cookbook:
        cookbook_name = cfg['name']
        cookbook = create_new_cookbook(
            cookbook_name, templatepack, cookbooks_home, force=force)

    for stencil in cfg['stencils']:
        stencil_set = stencil.pop('stencil_set')
        name = stencil.pop('name')
        # items left un-popped are **options
        update_cookbook(
            cookbook.path, templatepack, stencil_set, name=name, **stencil)
    return cookbook


def update_cookbook(cookbook_path, templatepack, stencilset_name, **options):

    force = options.get('force', False)
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

    files = {
        # files.keys() are template paths, files.values() are target paths
        # {path to template: rendered target path, ... }
        os.path.join(stencilset.path, tpl): os.path.join(cookbook.path, tgt)
        for tgt, tpl in stencil['files'].iteritems()
    }

    template_map = {
        'options': stencil['options'],
        'cookbook': cookbook.metadata.copy(),
    }
    template_map['cookbook']['year'] = datetime.datetime.now().year
    filetable = templating.render_templates(
        *files.keys(), **template_map)
    for tpl_path, content in filetable:
        target_path = files[tpl_path]
        needdir = os.path.dirname(target_path)
        assert needdir, "Target should have valid parent dir"
        try:
            os.makedirs(needdir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        if os.path.isfile(target_path):
            if force:
                LOG.warning("Forcing overwrite of existing file %s.",
                            target_path)
            else:
                print("Skipping existing file %s" % target_path)
                LOG.info("Skipping existing file %s", target_path)
                continue

        with open(target_path, 'w') as newfile:
            print("Writing rendered file %s" % target_path)
            LOG.info("Writing rendered file %s", target_path)
            newfile.write(content)

    if metadata_writelines:
        cookbook.write_metadata_dependencies(
            metadata_writelines)

    if berksfile_writelines:
        cookbook.write_berksfile_dependencies(
            berksfile_writelines)


def create_new_cookbook(cookbook_name, templatepack,
                        cookbooks_home, force=False):
    """Create a new cookbook.

    :param cookbook_name: Name of the new cookbook.
    :param templatepack: Path to templatepack.
    :param cookbooks_home: Target dir for new cookbook.

    TODO:
        return something, like files added or path to new cookbook or both
    """
    cookbooks_home = utils.normalize_path(cookbooks_home)

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
        if not os.path.exists(cookbooks_home):
            raise ValueError("Target cookbook dir %s does not exist."
                             % os.path.relpath(cookbooks_home))

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
        target_dir = os.path.join(cookbooks_home, cookbook_name, path)
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
            cookbooks_home, cookbook_name, path_map[orig_path])
        needdir = os.path.dirname(target_path)
        assert needdir, "Target should have valid parent dir"
        try:
            os.makedirs(needdir)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        if os.path.isfile(target_path):
            if force:
                LOG.warning("Forcing overwrite of existing file %s.",
                            target_path)
            else:
                LOG.info("Skipping existing file %s", target_path)
                continue
        else:
            with open(target_path, 'w') as newfile:
                LOG.info("Writing rendered file %s", target_path)
                newfile.write(content)
    return book.CookBook(os.path.join(cookbooks_home, cookbook_name))
