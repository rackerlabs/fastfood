require_relative 'spec_helper'

describe '|{ cookbook['name'] }|::|{ options['name'] }|' do
  let(:chef_run) do
    ChefSpec::Runner.new.converge('|{ cookbook['name'] }|::|{ options['name'] }|')
  end

  it 'includes the pg-multi::pg_master recipe' do
    expect(chef_run).include_recipe('pg-multi::pg_master')
  end

{% if options['database'] != "" %}
  it 'creates the database |{ options['database'] }||' do
    expect(chef_run).create_postgresql_database(|{ options['database'] }|)
  end
{% endif %}
end
