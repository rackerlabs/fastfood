#
# Cookbook Name:: |{ cookbook['name'] }|
# Recipe :: |{ options['name'] }|
#
# Copyright |{ cookbook['year'] }|, Rackspace
#
{% if options['databag'] != "" %}
postgres_creds = Chef::EncryptedDataBagItem.load(
  '|{ options['databag'] }|',
  node.chef_environment
)
{% end %}
{% if options['openfor'] != "" %}
search_string = "chef_environment:#{node.chef_environment} AND tags:|{ options['openfor'] }|"
search_add_iptables_rules(
  search_string,
  'INPUT',
  "-m tcp -p tcp --dport #{node['postgresql']['config']['port']} -j ACCEPT",
  70,
  'access to postgres'
)
{% if options['database'] != "" %}
include_recipe 'chef-sugar'

app_nodes = search(:node, search_string)
unless app_nodes.empty?
  app_nodes.each do |anode|
    node.default['postgresql']['pg_hba'] << {
      command: '# authorize app server',
      type: 'host',
      {% if options['databag'] != "" %}
      user: postgres_creds['username'],
      {% else %}
      user: |{ options['user'] }|,
      {% end %}
      addr: "#{best_ip_for(anode)}/32",
      method: 'md5'
    }
  end
end
{% end %}
{% end %}
include_recipe 'pg-multi'
include_recipe 'database::postgres'
{% if options['database'] != "" %}
conn = {
  host: 'localhost',
  username: 'postgres',
  password: node['postgresql']['password']['postgres']
}
{% if options['databag'] != "" %}
postgresql_database |{ options['database'] }| do
  connection conn
  action :create
end

postgresql_database_user postgres_creds['username'] do
  connection conn
  action :create
  database_name |{ qstring(options['database']) }|
  password postgres_creds['password']
  privileges [:all]
end
{% else %}
  postgresql_database |{ options['database'] }| do
  connection conn
  action :create
end

postgresql_database_user |{ options['user'] }| do
  connection conn
  action :create
  database_name |{ qstring(options['database']) }|
  password |{ options['password'] }|
  privileges [:all]
end
{% end %}
{% end %}
