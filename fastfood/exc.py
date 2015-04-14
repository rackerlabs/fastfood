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

"""Fastfood Exceptions."""

import re

_SPLITCASE_RE = re.compile(r'[A-Z][^A-Z]*')


class FastfoodError(Exception):

    """Base class for all exceptions raised by fastfood."""


class FastfoodStencilSetNotListed(FastfoodError):

    """Stencil set specified was not listed in the templatepack manifest."""


class FastfoodStencilInvalidPath(FastfoodError):

    """Specified path to stencil set does not exist."""


class FastfoodStencilSetMissingManifest(FastfoodError):

    """Stencil set is missing a manifest.json file."""


class FastfoodTemplatePackAttributeError(AttributeError, FastfoodError):

    """Invalid stencilset request from TemplatePack."""


def get_friendly_title(err):
    """Turn class, instance, or name (str) into an eyeball-friendly title.

    E.g. FastfoodStencilSetNotListed --> 'Stencil Set Not Listed'
    """
    if isinstance(err, basestring):
        string = err
    else:
        try:
            string = err.__name__
        except AttributeError:
            string = err.__class__.__name__
    split = _SPLITCASE_RE.findall(string)
    if not split:
        split.append(string)
    if len(split) > 1 and split[0] == 'Fastfood':
        split.pop(0)

    return " ".join(split)
