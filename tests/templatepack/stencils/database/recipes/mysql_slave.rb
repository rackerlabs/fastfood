#
# Cookbook Name:: |{ cookbook['name'] }|
# Recipe :: |{ options['name'] }|
#
# Copyright |{ cookbook['year'] }|, Rackspace
#

include_recipe 'mysql-multi::mysql_slave'

{% if options['openfor'] != "" %}
search_string = "chef_environment:#{node.chef_environment} AND tags:|{ options['openfor'] }|"
search_add_iptables_rules(
  search_string,
  'INPUT',
  "-m tcp -p tcp --dport #{node['mysql']['port']} -j ACCEPT",
  70,
  'access to mysql'
)
{% end %}
