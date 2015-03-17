fastfood
========

Helps build cookbooks faster by pre-templating parts and exposing
options in a command line and config friendly way.

### Installation
The latest release of fastfood can be installed via pip:
```
pip install fastfood
```
An alternative install method would be manually installing it leveraging
`setup.py`:

```
git clone https://github.com/rackerlabs/fastfood
cd fastfood
python setup.py install
```

### Command Line Usage

#### gen
Generates or updates an existing cookbook by rendering a given stencil_set
followed by options.

Ex:
```
fastfood gen -c /home/me/cookbooks/mycookbook redis name:redis_recipe
```

#### new
Creates a new cookbook using a given templatepacks base files.

Ex:
```
fastfood new mycookbook
```

#### build
Generates a new cookbook or updates an existing cookbook from a fastfood.json
file.

Example Template:
```json
{
  "name": "mycookbook",
  "stencils": [
    {
      "stencil_set": "rabbitmq",
      "openfor": "myapp"
    },
    {
      "stencil_set": "rails",
      "stencil": "nginx",
      "name": "myapp",
      "tag": "myapp"
    }
  ]
}
```

Ex:
```
fastfood build fastfood.json
```

### Template Notes
Fastfood uses the [Jinja2](http://jinja.pocoo.org/) templating engine with
2 modifications.

#### qstring()
There is a helper method added to jinja2 for fastfood called qstring, it
takes in an argument and if that argument does not match a Chef node
attributes (node['mysomething'] | node.chef_environment) it will wrap that argument
in a string otherwise it just returns the argument.

```ruby
qstring("node['mysomething']")

renders as

node['mysomething']
```

and

```
qstring("mynonchefstr")

renders as

"mynonchefstr"
```

#### jinja variable
Because the traditional jinja2 variable start and end strings can conflict
with Ruby code fastfood uses '|{' and '}|' to represent a jinja2 variable.

```
|{ options['name'] }|
```
