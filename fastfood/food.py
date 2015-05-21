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


def _determine_selected_stencil(stencil_set, stencil_definition):
    """Determine appropriate stencil name for stencil definition


    Given a fastfood.json stencil definition with a stencil set, figure out
    what the name of the stencil within the set should be, or use the default
    """

    if 'stencil' not in stencil_definition:
        selected_stencil_name = stencil_set.manifest.get('default_stencil')
    else:
        selected_stencil_name = stencil_definition.get('stencil')

    if not selected_stencil_name:
        raise ValueError("No stencil name, within stencil set %s, specified."
                         % stencil_definition['name'])

    return selected_stencil_name


def _build_template_map(cookbook, cookbook_name, stencil):
    """Build a map of variables for this generated cookbook and stencil


    Get template variables from stencil option values, adding the default ones
    like cookbook and cookbook year.
    """

    template_map = {
        'cookbook': {"name": cookbook_name},
        'options': stencil['options']
    }

    # Cookbooks may not yet have metadata, so we pass an empty dict if so
    try:
        template_map['cookbook'] = cookbook.metadata.to_dict().copy()
    except ValueError:
        # ValueError may be returned if this cookbook does not yet have any
        # metadata.rb written by a stencil. This is okay, as everyone should
        # be using the base stencil first, and then we'll try to call
        # cookbook.metadata again in this method later down.
        pass

    template_map['cookbook']['year'] = datetime.datetime.now().year
    return template_map


def _render_templates(files, filetable, written_files, force, open_mode='w'):
    """Write template contents from filetable into files


    Using filetable for the rendered templates, and the list of files, render
    all the templates into actual files on disk, forcing to overwrite the file
    as appropriate, and using the given open mode for the file
    """

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
            elif target_path in written_files:
                LOG.warning("Previous stencil has already written file %s.",
                            target_path)
            else:
                print("Skipping existing file %s" % target_path)
                LOG.info("Skipping existing file %s", target_path)
                continue

        with open(target_path, open_mode) as newfile:
            print("Writing rendered file %s" % target_path)
            LOG.info("Writing rendered file %s", target_path)
            newfile.write(content)
            written_files.append(target_path)


def build_cookbook(build_config, templatepack_path,
                   cookbooks_home, force=False):
    """Build a cookbook from a fastfood.json file.

    Can build on an existing cookbook, otherwise this will
    create a new cookbook for you based on your templatepack.
    """

    with open(build_config) as cfg:
        cfg = json.load(cfg)

    cookbook_name = cfg['name']
    template_pack = pack.TemplatePack(templatepack_path)

    written_files = []
    cookbook = create_new_cookbook(cookbook_name, cookbooks_home)

    for stencil_definition in cfg['stencils']:

        selected_stencil_set_name = stencil_definition.get('stencil_set')
        stencil_set = template_pack.load_stencil_set(selected_stencil_set_name)

        selected_stencil_name = _determine_selected_stencil(
            stencil_set,
            stencil_definition
            )

        stencil = stencil_set.get_stencil(selected_stencil_name,
                                          **stencil_definition)

        updated_cookbook = process_stencil(
            cookbook,
            cookbook_name,  # in case no metadata.rb yet
            template_pack,
            force,
            stencil_set,
            stencil,
            written_files
            )

    return written_files, updated_cookbook


def process_stencil(cookbook, cookbook_name, template_pack,
                    force_argument, stencil_set, stencil, written_files):
    """Process the stencil requested, writing any missing files as needed.

    The stencil named 'stencilset_name' should
    be one of templatepack's stencils.
    """

    # force can be passed on the command line or forced in a stencil's options
    force = force_argument or stencil['options'].get('force', False)

    stencil['files'] = stencil.get('files') or {}
    files = {
        # files.keys() are template paths, files.values() are target paths
        # {path to template: rendered target path, ... }
        os.path.join(stencil_set.path, tpl): os.path.join(cookbook.path, tgt)
        for tgt, tpl in stencil['files'].iteritems()
    }

    stencil['partials'] = stencil.get('partials') or {}
    partials = {
        # files.keys() are template paths, files.values() are target paths
        # {path to template: rendered target path, ... }
        os.path.join(stencil_set.path, tpl): os.path.join(cookbook.path, tgt)
        for tgt, tpl in stencil['partials'].iteritems()
    }

    template_map = _build_template_map(cookbook, cookbook_name, stencil)

    filetable = templating.render_templates(*files.keys(), **template_map)
    _render_templates(files, filetable, written_files, force)

    parttable = templating.render_templates(*partials.keys(), **template_map)
    _render_templates(partials, parttable, written_files, force, open_mode='a')

    # merge metadata.rb dependencies
    stencil_metadata_deps = {'depends': stencil.get('dependencies', {})}
    stencil_metadata = book.MetadataRb.from_dict(stencil_metadata_deps)
    cookbook.metadata.merge(stencil_metadata)

    # merge Berksfile dependencies
    stencil_berks_deps = {'cookbook': stencil.get('berks_dependencies', {})}
    stencil_berks = book.Berksfile.from_dict(stencil_berks_deps)
    cookbook.berksfile.merge(stencil_berks)

    return cookbook


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
