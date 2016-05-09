#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys
import signal
import shutil
import logging
import subprocess
from gi.repository import GLib
from fwp_util import FwpUtil
from fwp_util import StdoutRedirector


class FwpDaemon:

    def __init__(self, param):
        self.param = param
        self.apacheProc = None

    def run(self):
        FwpUtil.mkDirAndClear(self.param.tmpDir)
        try:
            sys.stdout = StdoutRedirector(os.path.join(self.param.tmpDir, "fpemud-portal.out"))
            sys.stderr = sys.stdout

            logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
            logging.getLogger().setLevel(logging.INFO)

            # start apache
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
            logging.shutdown()
            shutil.rmtree(self.param.tmpDir)

    def _sigHandlerINT(self, signum):
        logging.info("SIGINT received.")
        self.param.mainloop.quit()

    def _sigHandlerTERM(self, signum):
        logging.info("SIGTERM received.")
        self.param.mainloop.quit()

    def _runApache(self):
        # make apache root directory
        apacheDir = os.path.join(self.param.tmpDir, "apache") 
        os.mkdir(apacheDir)

        # generate apache config file
        buf = ""
        buf += "LoadModule log_config_module      /usr/lib/apache2/modules/mod_log_config.so\n"
        buf += "LoadModule env_module             /usr/lib/apache2/modules/mod_env.so\n"
        buf += "LoadModule unixd_module           /usr/lib/apache2/modules/mod_unixd.so\n"	
        buf += "LoadModule alias_module           /usr/lib/apache2/modules/mod_alias.so\n"
        buf += "LoadModule cgi_module             /usr/lib/apache2/modules/mod_cgi.so\n"
        buf += "\n"
        buf += "LoadModule ssl_module             /usr/lib/apache2/modules/mod_ssl.so\n"
        buf += "LoadModule auth_basic_module      /usr/lib/apache2/modules/mod_auth_basic.so\n"
        buf += "LoadModule authn_core_module      /usr/lib/apache2/modules/mod_authn_core.so\n"
        buf += "LoadModule authn_file_module      /usr/lib/apache2/modules/mod_authn_file.so\n"
        buf += "LoadModule authz_core_module      /usr/lib/apache2/modules/mod_authz_core.so\n"
        buf += "LoadModule authz_user_module      /usr/lib/apache2/modules/mod_authz_user.so\n"
        buf += "\n"
        buf += "\n"
        buf += "ServerName $(hostname)\n"        
        buf += "DocumentRoot \"%s\"\n" % (self.param.shareDir)        
        buf += "\n"        
        buf += "PidFile \"%s\"\n" % (os.path.join(apacheDir, "apache.pid"))	
        buf += "ErrorLog \"%s\"\n" % (os.path.join(apacheDir, "error.log"))
        buf += "LogFormat \"%h %l %u %t \\\"%r\\\" %>s %b \\\"%{Referer}i\\\" \\\"%{User-Agent}i\\\"\" common\n"
        buf += "CustomLog \"%s\" common\n" % (os.path.join(apacheDir, "access.log"))
        buf += "\n"
        buf += "User fpemud-portal\n"
        buf += "Group fpemud-portal\n"
        buf += "\n"
        buf += "Listen %d https\n" % (self.param.listenPort)
        buf += "\n"
        buf += "SSLEngine on\n"        
        buf += "SSLProtocol all\n"
        buf += "SSLCertificateFile \"%s\"\n" % (self.param.certFile)
        buf += "SSLCertificateKeyFile \"%s\"\n" % (self.param.keyFile)
        buf += "\n"
        buf += "<Directory \"%s\">\n" % (self.param.shareDir)
        buf += "    AuthType Basic\n"
        buf += "    AuthName \"Web Portal for Fpemud\"\n"
        buf += "    AuthBasicProvider file\n"
        buf += "    AuthUserFile \"%s\"\n" % (self.param.htpasswdFile)
        buf += "    Require valid-user\n"
        buf += "</Directory>\n"
        buf += "\n"
        cfgf = os.path.join(apacheDir, "apache.conf")
        with open(cfgf, "w") as f:
            f.write(buf)

        # run apache process
        cmd = "/usr/sbin/apache2 -d \"%s\" -f \"%s\" -DFOREGROUND" % (apacheDir, cfgf)
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True)

        return proc