#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os


class FwpParam:

    def __init__(self):
        self.libDir = "/usr/lib/fpemud-portal"
        self.shareDir = "/usr/share/fpemud-portal"
        self.varDir = "/var/fpemud-portal"
        self.runDir = "/run/fpemud-portal"
        self.tmpDir = "/tmp/fpemud-portal"

        self.gitlabDir = os.path.join(self.varDir, "gitlab")

        self.user = "fpemud-portal"
        self.group = "fpemud-portal"

        self.caCertFile = os.path.join(self.varDir, "ca-cert.pem")
        self.caPrivkeyFile = os.path.join(self.varDir, "ca-prikey.pem")
        self.certFile = os.path.join(self.varDir, "cert.pem")
        self.privkeyFile = os.path.join(self.varDir, "prikey.pem")
        self.htpasswdFile = os.path.join(self.varDir, "htpasswd")

        self.httpRedirect = True

        self.mainloop = None
