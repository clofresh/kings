# General stuff
[
  "vim",
  "sysstat",
  "curl",
  "git",
  "rake",
  "supervisor",
].each do |p|
  package p
end

[
  "/usr/local",
  "/usr/local/bin",
  "/usr/local/etc",
  "/etc/chef",
  "/var/chef",
].each do |dir|
  directory dir do
    mode "0755"
  end
end

chef_node_json = "/usr/local/etc/chef-node.json"
chef_solo_log = "/var/log/chef/solo.log"
local_chef_solo_bin = "/usr/local/bin/chef-solo"

file chef_solo_log do
  mode "0644"
  action :create_if_missing
end

cookbook_file chef_node_json do
  mode "0644"
end

file local_chef_solo_bin do
  action :create
  mode "0755"
  content "/usr/bin/chef-solo -j #{chef_node_json}"
end

cron "chef-solo" do
  minute "*/#{node[:chef][:frequency]}"
  command "#{local_chef_solo_bin} 2>&1 >> #{chef_solo_log}"
end

cookbook_file "/etc/sudoers" do
  mode "0440"
end

