#
# Cookbook Name:: kings
# Recipe:: default
#
# Copyright 2012, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

# Kings dependencies

kings_user = node[:kings][:user]
kings_group = node[:kings][:group]

execute "adduser #{kings_user}" do
  not_if "id #{kings_user}"
end



