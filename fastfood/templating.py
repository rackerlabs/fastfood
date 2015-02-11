"""Jinja templating."""

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
