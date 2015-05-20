require_relative 'spec_helper'

describe '|{ cookbook['name'] }|::default' do
  let(:chef_run) do
    ChefSpec::Runner.new.converge('|{ cookbook['name'] }|::default')
  end
end
