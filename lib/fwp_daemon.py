#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys
import signal
import shutil
import logging
import socket
import subprocess
from gi.repository import GLib
from fwp_util import FwpUtil
from fwp_util import StdoutRedirector
from fwp_serv_git_mirror import FwpServiceGitMirror


class FwpDaemon:

    def __init__(self, param):
        self.param = param
        self.servList = []
        self.apacheProc = None

    def run(self):
        FwpUtil.mkDirAndClear(self.param.tmpDir)
        try:
            sys.stdout = StdoutRedirector(os.path.join(self.param.tmpDir, "fpemud-portal.out"))
            sys.stderr = sys.stdout

            logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
            logging.getLogger().setLevel(logging.INFO)

            # create services
            self.servList.append(FwpServiceGitMirror(self.param))

            # start services
            for serv in self.servList:
                serv.start()

            # start apache
            os.mkdir(self.param.apacheDir)
            os.mkdir(self.param.apacheSubSiteCfgDir)
            for i in range(0, len(self.servList)):
                serv = self.servList[i]
                fn = os.path.join(self.param.apacheSubSiteCfgDir, "%02d-%s.conf" % (i + 1, serv.getName()))
                with open(fn, "w") as f:
                    f.write(serv.getApacheConfSnippet())
            self.apacheProc = self._runApache()
            logging.info("apache started.")

            # write pid file
            with open(os.path.join(self.param.tmpDir, "fpemud-portal.pid"), "w") as f:
                f.write(str(os.getpid()))

            # start main loop
            logging.info("Mainloop begins.")
            self.param.mainloop = GLib.MainLoop()
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGINT, self._sigHandlerINT, None)
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, self._sigHandlerTERM, None)
            self.param.mainloop.run()
            logging.info("Mainloop exits.")
        finally:
            if self.apacheProc is not None:
                self.apacheProc.terminate()
                self.apacheProc.wait()

            i = len(self.servList) - 1
            while i >= 0:
                self.servList[i].stop()
                i = i - 1

            logging.shutdown()
            shutil.rmtree(self.param.tmpDir)

    def _sigHandlerINT(self, signum):
        logging.info("SIGINT received.")
        self.param.mainloop.quit()

    def _sigHandlerTERM(self, signum):
        logging.info("SIGTERM received.")
        self.param.mainloop.quit()

    def _runApache(self):
        # generate apache config file
        buf = ""
        buf += "LoadModule alias_module           /usr/lib/apache2/modules/mod_alias.so\n"
        buf += "LoadModule log_config_module      /usr/lib/apache2/modules/mod_log_config.so\n"
        buf += "LoadModule env_module             /usr/lib/apache2/modules/mod_env.so\n"
        buf += "LoadModule dir_module             /usr/lib/apache2/modules/mod_dir.so\n"
        #buf += "LoadModule mime_module            /usr/lib/apache2/modules/mod_mime.so\n"
        buf += "LoadModule unixd_module           /usr/lib/apache2/modules/mod_unixd.so\n"
        buf += "\n"
        buf += "LoadModule rewrite_module         /usr/lib/apache2/modules/mod_rewrite.so\n"
        buf += "LoadModule ssl_module             /usr/lib/apache2/modules/mod_ssl.so\n"
        buf += "LoadModule auth_basic_module      /usr/lib/apache2/modules/mod_auth_basic.so\n"
        buf += "LoadModule authn_core_module      /usr/lib/apache2/modules/mod_authn_core.so\n"
        buf += "LoadModule authn_file_module      /usr/lib/apache2/modules/mod_authn_file.so\n"
        buf += "LoadModule authz_core_module      /usr/lib/apache2/modules/mod_authz_core.so\n"
        buf += "LoadModule authz_user_module      /usr/lib/apache2/modules/mod_authz_user.so\n"
        buf += "\n"
        buf += "LoadModule cgi_module             /usr/lib/apache2/modules/mod_cgi.so\n"
        buf += "LoadModule passenger_module       /usr/lib/apache2/modules/mod_passenger.so\n"
        buf += "\n"
        buf += "\n"
        buf += "ServerName %s\n" % (socket.gethostname())
        buf += "DocumentRoot \"%s\"\n" % (self.param.shareDir)
        buf += "\n"
        buf += "PidFile \"%s\"\n" % (os.path.join(self.param.apacheDir, "apache.pid"))
        buf += "ErrorLog \"%s\"\n" % (os.path.join(self.param.apacheDir, "error.log"))
        buf += "LogFormat \"%h %l %u %t \\\"%r\\\" %>s %b \\\"%{Referer}i\\\" \\\"%{User-Agent}i\\\"\" common\n"
        buf += "CustomLog \"%s\" common\n" % (os.path.join(self.param.apacheDir, "access.log"))
        buf += "\n"
        buf += "User %s\n" % (self.param.user)
        buf += "Group %s\n" % (self.param.group)
        buf += "\n"
        buf += "PassengerRoot /usr/lib64/ruby/vendor_ruby/phusion_passenger/locations.ini\n"
        buf += "PassengerDefaultRuby /usr/bin/ruby\n"
        buf += "\n"
        buf += "<Directory /usr/share/gitweb/gitweb.cgi>\n"
        buf += "    Options +ExecCGI\n"
        buf += "</Directory>\n"
        buf += "\n"
        if self.param.httpRedirect:
            buf += "Listen 80 http\n"
            buf += "<VirtualHost *:80>\n"
            buf += "    RewriteEngine On\n"
            buf += "    RewriteCond %{HTTPS} off\n"
            buf += "    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI}\n"
            buf += "</VirtualHost>\n"
            buf += "\n"
        if True:
            buf += "Listen 443 https\n"
            buf += "<VirtualHost *:443>\n"
            buf += "    SSLEngine on\n"
            buf += "    SSLProtocol all\n"
            buf += "    SSLCertificateFile \"%s\"\n" % (self.param.certFile)
            buf += "    SSLCertificateKeyFile \"%s\"\n" % (self.param.privkeyFile)
            buf += "    \n"
            buf += "    <Directory \"%s\">\n" % (self.param.shareDir)
            buf += "        AllowOverride None\n"
            buf += "        AuthType Basic\n"
            buf += "        AuthName \"Web Portal for Fpemud\"\n"
            buf += "        AuthBasicProvider file\n"
            buf += "        AuthUserFile \"%s\"\n" % (self.param.htpasswdFile)
            buf += "        Require valid-user\n"
            buf += "    </Directory>\n"
            buf += "</VirtualHost>\n"
            buf += "\n"
        buf += "Include \"%s\"\n" % (self.param.apacheSubSiteCfgDir)
        cfgf = os.path.join(self.param.apacheDir, "httpd.conf")
        with open(cfgf, "w") as f:
            f.write(buf)

        # run apache process
        cmd = "/usr/sbin/apache2 -d \"%s\" -f \"%s\" -DFOREGROUND" % (self.param.apacheDir, cfgf)
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True)

        return proc


# RailsBaseURI /gitlab
# <Directory /var/www/gitlab>
#    Options -MultiViews
# </Directory>
