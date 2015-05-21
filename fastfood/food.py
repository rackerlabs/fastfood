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


def build_cookbook(build_config, templatepack, cookbooks_home, force=False):
    """Build a cookbook from a fastfood.json file.

    Can build on an existing cookbook, otherwise this will
    create a new cookbook for you based on your templatepack.
    """

    with open(build_config) as cfg:
        cfg = json.load(cfg)

    cookbook_name = cfg['name']
    written_files = []
    cookbook = create_new_cookbook(cookbook_name, cookbooks_home)

    for stencil in cfg['stencils']:
        stencil_set = stencil.pop('stencil_set')
        # items left un-popped are **options
        files, updated_cookbook = process_stencil(
            cookbook,
            cookbook_name,  # pass this in case metadata.rb isn't written yet
            templatepack,
            force,
            stencil_set,
            **stencil
            )
        written_files.extend(files)
    return written_files, cookbook


def process_stencil(cookbook, cookbook_name, templatepack,
                    force_argument, stencilset_name, **options):
    """Process the stencil + options, writing any missing files as needed.

    The stencil named 'stencilset_name' should
    be one of templatepack's stencils.
    """

    # force can be passed on the command line or forced in a stencil's options
    force = force_argument or options.get('force', False)
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
        'cookbook': {"name": cookbook_name},
        'options': stencil['options'],
    }

    # Cookbooks may not yet have metadata, so we pass an empty dict if so
    try:
        template_map['cookbook'] = cookbook.metadata.to_dict().copy()
    except ValueError as err:
        # ValueError may be returned if this cookbook does not yet have any
        # metadata.rb written by a stencil. This is okay, as everyone should
        # be using the base stencil first, and then we'll try to call
        # cookbook.metadata again in this method later down.
        pass

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


def create_new_cookbook(cookbook_name, cookbooks_home):
    """Create a new cookbook.

    :param cookbook_name: Name of the new cookbook.
    :param cookbooks_home: Target dir for new cookbook.
    """
    cookbooks_home = utils.normalize_path(cookbooks_home)

    if not os.path.exists(cookbooks_home):
        raise ValueError("Target cookbook dir %s does not exist."
                         % os.path.relpath(cookbooks_home))

    target_dir = os.path.join(cookbooks_home, cookbook_name)
    LOG.debug("Creating dir -> %s", target_dir)
    try:
        os.makedirs(target_dir)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
        else:
            LOG.info("Skipping existing directory %s", target_dir)

    cookbook_path = os.path.join(cookbooks_home, cookbook_name)
    cookbook = book.CookBook(cookbook_path)

    return cookbook
