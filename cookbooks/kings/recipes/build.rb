# Kings build environment

kings_user = node[:kings][:user]
kings_group = node[:kings][:group]
kings_virtualenv = node[:kings][:virtualenv]

build_dir = "/usr/local/build"
kings_build_number = build_dir + "/var/kings-build-number"
kings_repo_dir = build_dir + "/kings"
kings_build_bin = "/usr/local/build/bin/kings-build"
kings_build_log = "/var/log/kings-build.log"

[
  build_dir,
  "/usr/local/build/bin",
  "/usr/local/build/var",
].each do |dir|
  directory dir do
    mode "0755"
    owner kings_user
    group kings_group
  end
end

# For storing the build number
file kings_build_number do
  mode "0644"
  owner kings_user
  group kings_group
  content "0"
  action :create_if_missing
end

# Checkout the kings repo but let the build script keep it up to date
git kings_repo_dir do
  user kings_user
  group kings_group
  repository node[:kings][:git_url]
  revision "master"
  action :checkout
end

# Build script
template kings_build_bin do
  source "kings-build.sh.erb"
  mode "0755"
  owner kings_user
  group kings_group
  variables(
    :kings_build_number => kings_build_number,
    :kings_repo_dir => kings_repo_dir,
    :kings_virtualenv => kings_virtualenv
  )
end

file kings_build_log do
  mode "0644"
  owner kings_user
  group kings_group
  action :create_if_missing
end

# Cron the build script to run every night at 2:01 AM 
cron "kings" do
  user kings_user
  hour "2"
  minute "1"
  command "#{kings_build_bin} 2>&1 >> #{kings_build_log}"
end


