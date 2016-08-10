#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
from fwp_util import FwpUtil


class FwpCommon:

    @staticmethod
    def makeDir(param, dirname):
        if os.path.exists(dirname):
            return
        FwpCommon.makeDir(param, os.path.dirname(dirname))
        os.mkdir(dirname)
        FwpUtil.shell("/bin/chown %s:%s \"%s\"" % (param.user, param.group, dirname))

    @staticmethod
    def writeFile(param, filename, buf, mode=None):
        FwpCommon.makeDir(param, os.path.dirname(filename))
        with open(filename, 'w') as f:
            f.write(buf)
        FwpUtil.shell("/bin/chown %s:%s \"%s\"" % (param.user, param.group, filename))
        if mode is not None:
            FwpUtil.shell("/bin/chmod " + mode + " \"%s\"" % (filename))
