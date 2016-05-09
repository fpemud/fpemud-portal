#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os


class FwpParam:

    def __init__(self):
        self.libDir = "/usr/lib/fpemud-portal"
        self.shareDir = "/usr/share/fpemud-portal"
        self.varDir = "/var/fpemud-portal"
        self.tmpDir = "/tmp/fpemud-portal"

        self.certFile = os.path.join(self.varDir, "cert.pem")
        self.keyFile = os.path.join(self.varDir, "prikey.pem")
        self.htpasswdFile = os.path.join(self.VarDir, "htpasswd")

        self.listenPort = 443

        self.mainloop = None
