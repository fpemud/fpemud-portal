#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys
import signal
import shutil
import logging
from gi.repository import GLib
from fwp_util import FwpUtil
from fwp_util import StdoutRedirector


class FwpDaemon:

    def __init__(self, param):
        self.param = param

    def run(self):
        FwpUtil.mkDirAndClear(self.param.tmpDir)
        try:
            sys.stdout = StdoutRedirector(os.path.join(self.param.tmpDir, "fpemud-portal.out"))
            sys.stderr = sys.stdout

            logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
            logging.getLogger().setLevel(logging.INFO)

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
