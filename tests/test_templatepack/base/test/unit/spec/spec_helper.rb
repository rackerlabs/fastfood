require 'chefspec'
require 'chefspec/berkshelf'

at_exit { ChefSpec::Converge.report! }
