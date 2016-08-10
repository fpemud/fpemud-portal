#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

class FwpServiceGitMirror:

    """
    This service is to provide a git mirror for:
      1. github.com
      2. 
    """

    def __init__(self, param):
        self.param = param

        self.myTmpDir = os.path.join(self.param.tmpDir, "git-mirror")

        self.myVarDir = os.path.join(self.param.varDir, "git-mirror")
        self.myVarDataDir = os.path.join(self.myVarDir, "root")
        self.myVarTmpDir = os.path.join(self.myVarDir, "tmp")

    def start(self):
        FwpCommon.makeDir(self.myTmpDir)
        FwpCommon.makeDir(self.myVarDataDir)
        FwpCommon.makeDir(self.myVarTmpDir)

        self._genGitWebCfg()

    def stop(self):
        pass

    def getApacheConfSnippet(self):
        buf = ""
        buf += "<Location /git-mirror>\n"
        buf += "    PassEnv GIT_DIR\n"
        buf += "    PassEnv GIT_EXEC_PATH\n"
        buf += "    PassEnv GITWEB_CONFIG\n"
        buf += "    DirectoryIndex gitweb.cgi\n"
        buf += "    <Location /git-mirror/gitweb.cgi>\n"
        buf += "        Options +ExecCGI\n"
        buf += "    </Location>\n"
        buf += "</Location>\n"



    def _genGitWebCfg(self):
        buf = ""
        buf += "#!/usr/bin/perl\n"
        buf += "\n"
        buf += "our $projectroot = \"%s\";\n" % (self.myRootDir)
        buf += "our $git_temp = \"%s\";\n" % (self.myTmpDir)
        buf += "our $projects_list = $projectroot;\n"
        buf += "\n"
        buf += "$feature{'remote_heads'}{'default'} = [1];\n"

        cfgf = os.path.join(self.myTmpDir, "gitweb-config.perl")
        with open(cfgf, "w") as f:
            f.write(cfgf)