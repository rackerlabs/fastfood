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

"""Jinja templating for Fastfood."""

import os

import jinja2

# create a jinja env, overriding delimiters
JINJA_ENV = jinja2.Environment(variable_start_string='|{',
                               variable_end_string='}|')

def render_templates(*files, **template_map):
    """Render jinja templates according to template_map.

    Return a list of [(path, result), (...)]
    """
    return list(render_templates_generator(*files, **template_map))


def render_templates_generator(*files, **template_map):
    """Render jinja templates according to template_map.

    Yields (path, result)
    """
    for path in files:
        if not os.path.isfile(path):
            raise ValueError("Template file %s not found"
                             % os.path.relpath(path))
        else:
            try:
                template = JINJA_ENV.from_string(open(path).read())
            except jinja2.TemplateSyntaxError as err:
                msg = ("Error rendering jinja2 template for file %s "
                       "on line %s. Error: %s"
                       % (path, err.lineno, err.message))
                raise type(err)(
                    msg, err.lineno, filename=os.path.basename(path))

            result = template.render(**template_map)
            yield path, result
