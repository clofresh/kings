task :default => [:build]

desc "Packages Kings code and content files into a Python egg"
task :build do
	sh "python setup.py egg_info -b _#{build_number} bdist_egg"
	egg_file = egg_file("kings")
	puts "Built #{egg_file}"
end

desc "Clears .pyc files, and the build and dist directories"
task :clean => "clean:all"
namespace :clean do
	task :all => [:pyc, :dist, :build]

	task :pyc do
		rm(FileList.new(File.join("**", "*.pyc")))
	end
	task :dist do
		rm_rf("dist")
	end
	task :build do
		rm_rf("build")
	end
end

# Helpers

def egg_file(package)
	filename = File.join("dist", [package, egg_version, "*.egg"].join("-"))
  %x[ls #{filename} | sort | tail -n 1].strip
end

def egg_version
	%x[python setup.py --version].strip + "_" + build_number
end

def build_number
  b_num = ENV["BUILD_NUMBER"] || "dev"
  git_hash = short_git_hash || "unknown"

  b_num + "_" + git_hash
end

def short_git_hash
  %x[git log --pretty=format:'%h' -n 1].strip
end

