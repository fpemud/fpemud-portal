#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
from fwp_util import FwpUtil
from fwp_serv_gitlab import FwpServiceGitlab


class FwpCmd:

    def __init__(self, param):
        self.param = param
        self.servGitlab = FwpServiceGitlab()

    def cmdInit(self):
        if not os.path.exists(self.param.gitlabDir):
            FwpUtil.printInfo(">> Initializing GitLab service...")
            self.servGitlab.setup()
        else:
            FwpUtil.printInfo(">> Upgrading GitLab service...")
            self.servGitlab.migrate()
        print("")
