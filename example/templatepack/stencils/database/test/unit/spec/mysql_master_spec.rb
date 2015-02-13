require_relative 'spec_helper'

describe '|{ cookbook['name'] }|::|{ options['name'] }|' do
  let(:chef_run) do
    ChefSpec::Runner.new.converge('|{ cookbook['name'] }|::|{ options['name'] }|')
  end

  it 'includes the mysql-multi::mysql_master recipe' do
    expect(chef_run).include_recipe('mysql-multi::mysql_master')
  end
  {% if options['database'] != "" %}
  it 'creates the mysql_database |{ options['database'] }|' do
    expect(chef_run).create_mysql_database(|{ options['database'] }|)
  end
{% endif %}
end
