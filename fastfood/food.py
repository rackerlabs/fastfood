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
    """Build a cookbook from a fastfood.json file.

    Can build on an existing cookbook, otherwise this will
    create a new cookbook for you based on your templatepack.
    """

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

    written_files = []
    if not cookbook:
        cookbook_name = cfg['name']
        files, cookbook = create_new_cookbook(
            cookbook_name, templatepack, cookbooks_home, force=force)
        written_files.extend(files)

    for stencil in cfg['stencils']:
        stencil_set = stencil.pop('stencil_set')
        # items left un-popped are **options
        files, updated_cookbook = update_cookbook(
            cookbook, templatepack, stencil_set, **stencil)
        written_files.extend(files)
        assert updated_cookbook is cookbook
    return written_files, cookbook


def update_cookbook(cookbook, templatepack, stencilset_name, **options):
    """Update the cookbook with the stencil + options.

    The stencil named 'stencilset_name' should
    be one of templatepack's stencils.
    """

    force = options.get('force', False)
    tmppack = pack.TemplatePack(templatepack)
    stencilset = tmppack.load_stencil_set(stencilset_name)

    if 'stencil' not in options:
        selected_stencil = stencilset.manifest.get('default_stencil')
    else:
        selected_stencil = options['stencil']

    if not selected_stencil:
        raise ValueError("No %s stencil specified." % stencilset_name)

    stencil = stencilset.get_stencil(selected_stencil, **options)

    files = {
        # files.keys() are template paths, files.values() are target paths
        # {path to template: rendered target path, ... }
        os.path.join(stencilset.path, tpl): os.path.join(cookbook.path, tgt)
        for tgt, tpl in stencil['files'].iteritems()
    }

    template_map = {
        'options': stencil['options'],
        'cookbook': cookbook.metadata.to_dict().copy(),
    }

    template_map['cookbook']['year'] = datetime.datetime.now().year
    filetable = templating.render_templates(*files.keys(), **template_map)
    written_files = []
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
            written_files.append(target_path)

    # merge metadata.rb dependencies
    stencil_metadata_deps = {'depends': stencil.get('dependencies', {})}
    stencil_metadata = book.MetadataRb.from_dict(stencil_metadata_deps)
    cookbook.metadata.merge(stencil_metadata)

    # merge Berksfile dependencies
    stencil_berks_deps = {'cookbook': stencil.get('berks_dependencies', {})}
    stencil_berks = book.Berksfile.from_dict(stencil_berks_deps)
    cookbook.berksfile.merge(stencil_berks)
    return written_files, cookbook


def create_new_cookbook(cookbook_name, templatepack,
                        cookbooks_home, force=False):
    """Create a new cookbook.

    :param cookbook_name: Name of the new cookbook.
    :param templatepack: Path to templatepack.
    :param cookbooks_home: Target dir for new cookbook.
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

    written_files = []
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
        with open(target_path, 'w') as newfile:
            LOG.info("Writing rendered file %s", target_path)
            written_files.append(target_path)
            newfile.write(content)

    return (written_files, book.CookBook(os.path.join(cookbooks_home,
                                                      cookbook_name)))
