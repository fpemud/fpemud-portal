#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import shutil
import subprocess
from fwp_util import FwpUtil
from fwp_common import FwpCommon


class FwpServiceGitlab:

    def __init__(self, param):
        self.param = param

        self.verCurFile = os.path.join(glob.glob("/opt/gitlab-*")[0], "VERSION")
        self.verRecFile = os.path.join(self.param.gitlabDir, "VERSION")

        self.dbCfgDir = os.path.join(self.param.gitlabDir, "config-mysql")
        self.gitlabCfgDir = os.path.join(self.param.gitlabDir, "config-gitlab")
        self.dbDataDir = os.path.join(self.param.gitlabDir, "mysql")
        self.repoDir = os.path.join(self.param.gitlabDir, "repositories")
        self.lfsObjDir = os.path.join(self.param.gitlabDir, "lfs-objects")

        self.dbSockFile = os.path.join(self.param.runDir, "gitlab-mysqld.sock")
        self.dbPidFile = os.path.join(self.param.runDir, "gitlab-mysqld.pid")

        self.myTmpDir = os.path.join(self.param.tmpDir, "gitlab")
        self.dbProc = None

    def setup(self):
        if os.path.exists(self.param.gitlabDir):
            return

        FwpCommon.makeDir(self.param.gitlabDir)
        try:
            # create mariadb config file
            self._generateMariaDbCfgFile()

            # create gitlab config files
            self._generateGitlabCfgFiles()

            # create gitlab database
            self._mountOverlayFs()
            dbProc = None
            try:
                FwpCommon.makeDir(self.dbDataDir)
                dbProc = self._runMariaDb()
                FwpUtil.shell("/usr/bin/ruby21 /usr/bin/bundle exec rake gitlab:setup RAILS_ENV=production")
            finally:
                if dbProc is not None:
                    dbProc.terminate()
                    dbProc.join()
                self._umountOverlayFs()

            # create gitlab directories
            FwpCommon.makeDir(self.repoDir)
            FwpCommon.makeDir(self.lfsObjDir)

            # record version
            shutil.copy2(self.verCurFile, self.verRecFile)
        except:
            shutil.rmtree(self.param.gitlabDir)
            raise

    def migrate(self):
        # --fixme, no exception code

        if FwpUtil.readFile(self.verCurFile) == FwpUtil.readFile(self.verRecFile):
            return

        # regenerate config files
        shutil.rmtree(self.dbCfgDir)
        self._generateMariaDbCfgFile()
        shutil.rmtree(self.gitlabCfgDir)
        self._generateGitlabCfgFiles()

        # migrate gitlab database
        self._mountOverlayFs()
        dbProc = None
        try:
            dbProc = self._runMariaDb()
            FwpUtil.shell("/usr/bin/ruby21 /usr/bin/bundle exec rake db:migrate RAILS_ENV=production")
            FwpUtil.shell("/usr/bin/ruby21 /usr/bin/bundle exec rake cache:clear RAILS_ENV=production")
            FwpUtil.shell("/usr/bin/ruby21 /usr/bin/bundle exec rake assets:clean RAILS_ENV=production")
            FwpUtil.shell("/usr/bin/ruby21 /usr/bin/bundle exec rake assets:precompile RAILS_ENV=production")
        finally:
            if dbProc is not None:
                dbProc.terminate()
                dbProc.join()
            self._umountOverlayFs()

        # record version
        shutil.copy2(self.verCurFile, self.verRecFile)

    def start(self):
        # start service
        FwpCommon.makeDir(self.myTmpDir)
        self._mountOverlayFs()
        try:
            self.dbProc = self._runMariaDb()
        except:
            if self.dbProc is not None:
                self.dbProc.terminate()
                self.dbProc.wait()
            shutil.rmtree(self.myTmpDir)
            raise
        finally:
            self._umountOverlayFs()

    def stop(self):
        if self.dbProc is not None:
            self.dbProc.terminate()
            self.dbProc.wait()
        shutil.rmtree(self.myTmpDir)

    def _generateMariaDbCfgFile(self):
        buf = ""
        buf += "[mysqld]\n"
        buf += "character-set-server		= utf8\n"
        buf += "user 						= %s\n" % (self.param.user)
        buf += "socket 						= %s\n" % (self.dbSockFile)
        buf += "pid-file                    = %s\n" % (self.dbPidFile)
        buf += "datadir 					= %s\n" % (self.dbDataDir)
        buf += "tmpdir                      = %s\n" % (self.myTmpDir)
        buf += "\n"
        FwpCommon.writeFile(os.path.join(self.dbCfgDir, "my.cnf"), buf)

    def _runMariaDb(self):
        cmd = "/usr/sbin/mysqld_safe --defaults-file=\"%s\"" % (os.path.join(self.dbCfgDir, "my.cnf"))
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True)
        return proc

    def _generateGitlabCfgFiles(self):
        # database.yml
        buf = ""
        buf += "production:\n"
        buf += "  adapter: mysql2\n"
        buf += "  encoding: utf8\n"
        buf += "  collation: utf8_general_ci\n"
        buf += "  reconnect: false\n"
        buf += "  database: gitlabhq_production\n"
        buf += "  pool: 10\n"
        buf += "  username: %s\n" % (self.param.user)
        buf += "  password: %s\n" % (self.param.user)
        buf += "  host: localhost\n"
        buf += "  socket: %s\n" % (self.dbSockFile)
        buf += "\n"
        buf += "\n"
        buf += "development:\n"
        buf += "  adapter: mysql2\n"
        buf += "  encoding: utf8\n"
        buf += "  collation: utf8_general_ci\n"
        buf += "  reconnect: false\n"
        buf += "  database: gitlabhq_development\n"
        buf += "  pool: 10\n"
        buf += "  username: %s\n" % (self.param.user)
        buf += "  password: %s\n" % (self.param.user)
        buf += "  host: localhost\n"
        buf += "  socket: %s\n" % (self.dbSockFile)
        buf += "\n"
        buf += "\n"
        buf += "test: &test\n"
        buf += "  adapter: mysql2\n"
        buf += "  encoding: utf8\n"
        buf += "  collation: utf8_general_ci\n"
        buf += "  reconnect: false\n"
        buf += "  database: gitlabhq_test\n"
        buf += "  pool: 10\n"
        buf += "  username: %s\n" % (self.param.user)
        buf += "  password: %s\n" % (self.param.user)
        buf += "  host: localhost\n"
        buf += "  socket: %s\n" % (self.dbSockFile)
        buf += "\n"
        FwpCommon.writeFile(os.path.join(self.gitlabCfgDir, "database.yml"), buf)

        # gitlab.yml
        buf = ""
        buf += "production: &base\n"
        buf += "  gitlab:\n"
        buf += "  host: localhost\n"
        buf += "  port: 80\n"
        buf += "  https: false\n"
        buf += "  relative_url_root: /gitlab\n"
        buf += "  user: %s\n" % (self.param.user)
        buf += "  email_enabled: false\n"                               # default is true, which is unsuitable for us
    # time_zone: 'UTC'
    # default_theme: 2 # default: 2
    # backup
        buf += "\n"
        buf += "  default_projects_features:\n"
        buf += "    issues: true\n"
        buf += "    merge_requests: true\n"
        buf += "    wiki: true\n"
        buf += "    snippets: false\n"
        buf += "    builds: true\n"
        buf += "\n"
        buf += "  repository_downloads_path: %s/repositories\n" % (self.myTmpDir)
        buf += "\n"
        buf += "  lfs:\n"
        buf += "    enabled: true\n"
        buf += "    storage_path: %s\n" % (self.lfsObjDir)
        buf += "\n"
        buf += "  gravatar:\n"
        buf += "    enabled: false\n"                                   # set to false since we don't interact with the outer world
        buf += "\n"
        buf += "  gitlab_shell:\n"
        buf += "    path:  /var/lib/gitlab-shell/\n"
        buf += "    repos_path:  %s/\n" % (self.repoDir)                # MUST NOT BE A SYMLINK!!!
        buf += "    hooks_path:  /var/lib/gitlab-shell/hooks/\n"
        buf += "    upload_pack: true\n"
        buf += "    receive_pack: true\n"
    # If you use non-standard ssh port you need to specify it
    # ssh_port: 22
        buf += "\n"
        buf += "  git:\n"                                               # --fixme, do we need to specify them?
        buf += "    bin_path: /usr/bin/git\n"
        buf += "    max_size: 20971520\n"                               # 20.megabytes
        buf += "    timeout: 10\n"
        buf += "\n"
        buf += "\n"
        buf += "development:\n"
        buf += "  <<: *base\n"
        buf += "\n"
        buf += "\n"
        buf += "test:\n"
        buf += "  <<: *base\n"
        buf += "\n"
        buf += "\n"
        buf += "staging:\n"
        buf += "  <<: *base\n"
        buf += "\n"
        FwpCommon.writeFile(os.path.join(self.gitlabCfgDir, "gitlab.yml"), buf)

        # initializers/relative_url.rb
        buf = ""
        buf += "Rails.application.configure do\n"
        buf += "  config.relative_url_root = \"/gitlab\"\n"
        buf += "end\n"
        FwpCommon.writeFile(os.path.join(self.gitlabCfgDir, "initializers", "relative_url.rb"), buf)

        # unicorn.rb
        # doubt: all the content related to preload-app is removed, it is good?
        buf = ""
        buf += "worker_processes 3\n"
        buf += "\n"
        buf += "# working_directory \"/opt/gitlabhq-8.7\"\n"
        buf += "\n"
        buf += "listen \"/opt/gitlabhq-8.7/tmp/sockets/gitlab.socket\", :backlog => 1024\n"
        buf += "\n"
        buf += "# timeout 60\n"
        buf += "\n"
        buf += "pid \"/opt/gitlabhq-8.7/tmp/pids/unicorn.pid\""
        buf += "\n"
        buf += "stderr_path \"/opt/gitlabhq-8.7/log/unicorn.stderr.log\""
        buf += "stdout_path \"/opt/gitlabhq-8.7/log/unicorn.stdout.log\""
        buf += "\n"
        buf += "check_client_connection false\n"
        buf += "\n"
        buf += "ENV['RAILS_RELATIVE_URL_ROOT'] = \"/gitlab\"\n"
        buf += "\n"
        FwpCommon.writeFile(os.path.join(self.gitlabCfgDir, "unicorn.rb"), buf)

# Edit /home/git/gitlab-shell/config.yml and append the relative path to the following line:
# gitlab_url: http://127.0.0.1/gitlab

# Make sure you have copied the supplied init script and the defaults file as stated in the installation guide. Then, edit /etc/default/gitlab and set in gitlab_workhorse_options the -authBackend setting to read like:
# -authBackend http://127.0.0.1:8080/gitlab

# After all the above changes recompile the assets. This is an important task and will take some time to complete depending on the server resources:
# cd /home/git/gitlab
# sudo -u git -H bundle exec rake assets:clean assets:precompile RAILS_ENV=production

        buf = ""
        buf += "paths_to_be_protected = [\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/users/password\",\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/users/sign_in\",\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/api/#{API::API.version}/session.json\",\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/api/#{API::API.version}/session\",\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/users\",\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/users/confirmation\",\n"
        buf += "  \"#{Rails.application.config.relative_url_root}/unsubscribes/\"\n"
        buf += "]\n"
        buf += "\n"
        buf += "# Create one big regular expression that matches strings starting with any of\n"
        buf += "# the paths_to_be_protected.\n"
        buf += "paths_regex = Regexp.union(paths_to_be_protected.map { |path| /\A#{Regexp.escape(path)}/ })\n"
        buf += "\n"
        buf += "unless Rails.env.test?\n"
        buf += "  Rack::Attack.throttle('protected paths', limit: 10, period: 60.seconds) do |req|\n"
        buf += "    if req.post? && req.path =~ paths_regex\n"
        buf += "      req.ip\n"
        buf += "    end\n"
        buf += "  end\n"
        buf += "end\n"
        FwpCommon.writeFile(os.path.join(self.gitlabCfgDir, "rack_attack.rb"), buf)

#           secrets.yml

    def _mountOverlayFs(self):
        ocfgdir = os.path.join("/opt", "gitlab8.7", "config")
        FwpUtil.shell("/bin/mount -t overlayfs -o ro,lowerdir=\"%s\",upperdir=\"%s\" overlayfs \"%s\"" % (ocfgdir, self.gitlabCfgDir, ocfgdir))

    def _umountOverlayFs(self):
        ocfgdir = os.path.join("/opt", "gitlab8.7", "config")
        FwpUtil.shell("/bin/umount \"%s\"" % (ocfgdir))
