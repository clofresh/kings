# Kings runtime environment

kings_user = node[:kings][:user]
kings_group = node[:kings][:group]
kings_virtualenv = node[:kings][:virtualenv]
kings_bin = "/usr/local/kings/python/bin/kings"
kings_config = "/usr/local/kings/etc/kings.ini"
kings_log = "/var/log/kings.log"

package "python-virtualenv"
package "libevent-dev"
package "python-dev"

[
  "/usr/local/kings",
  "/usr/local/kings/etc",
].each do |dir|
  directory dir do
    mode "0755"
    owner kings_user
    group kings_group
  end
end

execute "set up virtualenv" do
  command "virtualenv --distribute #{kings_virtualenv} && chown -R #{kings_user}:#{kings_group} #{kings_virtualenv}"
  not_if do
    File.exists? kings_virtualenv
  end
end

file kings_log do
  mode "0644"
  owner kings_user
  group kings_group
  action :create_if_missing
end

template "/etc/sudoers.d/kings" do
  source "kings.sudoers.erb"
  mode "0440"
  variables :kings_user => kings_user
end

template "/etc/supervisor/conf.d/kings.conf" do
  source "kings.supervisor.conf.erb"
  mode "0644"
  variables(
    :kings_bin    => kings_bin,
    :kings_config => kings_config,
    :kings_log    => kings_log
  )
end

template kings_config do
  source "kings.ini.erb"
  mode "0644"
  variables(
    :kings_port => node[:kings][:port]
  )
end




