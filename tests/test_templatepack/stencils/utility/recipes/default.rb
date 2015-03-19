#
# Cookbook Name:: |{ cookbook['name'] }|
# Recipe :: |{ options['name'] }|
#
# Copyright |{ cookbook['year'] }|, Rackspace
#

node.default['authorization']['sudo']['passwordless'] = |{ options['sudo'] }|
node.default['platformstack']['omnibus_updater']['enabled'] = false

include_recipe 'rackops_rolebook::default'
include_recipe 'users::sysadmins'
include_recipe 'sudo::default'
