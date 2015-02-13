#
# Cookbook Name:: |{ cookbook['name'] }|
# Recipe :: |{ options['name'] }|
#
# Copyright |{ cookbook['year'] }|, Rackspace
#

include_recipe 'mysql-multi::mysql_master'

{% if options['openfor'] != "" %}
search_string = "chef_environment:#{node.chef_environment} AND tags:|{ options['openfor'] }|"
search_add_iptables_rules(
  search_string,
  'INPUT',
  "-m tcp -p tcp --dport #{node['mysql']['port']} -j ACCEPT",
  70,
  'access to mysql'
)
{% endif %}

{% if options['database'] != "" %}
conn = {
  host:  'localhost',
  username: 'root',
  password: node['mysql']['server_root_password']
}

include_recipe 'database::mysql'
{% if options['databag'] != "" %}
mysql_creds = Chef::EncryptedDataBagItem.load(
  '|{ options['databag'] }|',
  node.chef_environment
)

mysql_database |{ qstring(options['database']) }| do
  connection conn
  action :create
end

mysql_database_user mysql_creds['username'] do
  connection conn
  password mysql_creds['password']
  database |{ qstring(options['database']) }|
  action :create
end
{% else %}
  mysql_database |{ qstring(options['database']) }| do
  connection conn
  action :create
end

mysql_database_user |{ qstring(options['user']) }| do
  connection conn
  password |{ qstring(options['password']) }|
  database_name |{ qstring(options['database']) }|
  action :create
end
{% endif %}
{% endif %}
