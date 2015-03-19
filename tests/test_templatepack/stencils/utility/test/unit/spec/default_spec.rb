require_relative 'spec_helper'

describe '|{ cookbook['name'] }|::|{ options['name'] }|' do
  let(:chef_run) do
    ChefSpec::Runner.new.converge('|{ cookbook['name'] }|::|{ options['name'] }|')
  end

  it 'includes the rackops_rolebook default recipe' do
    expect(chef_run).to include_recipe('rackops_rolebook::default')
  end

  it 'includes the users sysadmins recipe' do
    expect(chef_run).to include_recipe('users::sysadmins')
  end

  it 'includes the sudo default recipe' do
    expect(chef_run).to include_recipe('sudo::default')
  end
end
