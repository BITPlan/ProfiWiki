"""
Created on 2023-04-01

@author: wf
"""
import json
import os

from basemkit.basetest import Basetest
from profiwiki.profiwiki_cmd import ProfiWikiCmd
from profiwiki.profiwiki_core import ProfiWiki
from profiwiki.version import Version


# from mwdocker.webscrape import WebScrape
class TestProfiWiki(Basetest):
    """
    test ProfiWiki
    """

    def setUp(self, debug=False, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        # change the port for the testwiki to not spoil a wiki on the default port
        self.pw = ProfiWiki(prefix="pwt1", port=11000)
        self.mwApp = None
        self.argv = [
            "--prefix",
            "pwt1",
            "--base_port",
            "11000",
            "--sql_base_port",
            "11001",
            "--apache",
            "test.bitplan.com"
        ]

    def testConfig(self):
        """
        test the config
        """
        config_dict = self.pw.config.as_dict()
        debug = self.debug
        if debug:
            print(json.dumps(config_dict, indent=2))
        self.assertEqual("pwt1", self.pw.config.prefix)

    def getProfiWiki(self, argv=[]):
        """
        get a profiwiki for the given command line arguments
        """
        pwcmd=ProfiWikiCmd(Version)
        pw = pwcmd.pw
        parser=ProfiWikiCmd.getArgParser(pwcmd,description=Version.license, version_msg="ProfiWiki for test")
        pw.args = parser.parse_args(argv)
        pw.config.fromArgs(pw.args)
        return pw

    def getMwApp(self, argv=None, forceRebuild: bool = False):
        """
        get the mediaWikiApp
        """
        if not argv:
            argv = self.argv
        self.pw = self.getProfiWiki(argv)
        self.pw.config.forceRebuild = forceRebuild
        mwApp = self.pw.getMwApp(withGenerate=forceRebuild)
        return mwApp

    def doStartMwApp(self, mwApp, forceRebuild: bool = True):
        """
        start MW App
        """
        if forceRebuild:
            mwApp.down(forceRebuild=forceRebuild)
        mwApp.start(forceRebuild=forceRebuild, withInitDB=forceRebuild)
        mwApp.check()

    def startMwApp(self):
        """
        start mediawiki application
        """
        forceRebuild = True
        mwApp = self.getMwApp(forceRebuild=forceRebuild)
        self.doStartMwApp(mwApp)
        return mwApp

    def test_system(self):
        """
        test system pre requisites
        """
        info = self.pw.system_info()
        debug = True
        if debug:
            print(info)

    def test_apache_config(self):
        """
        test the apache configuration handling
        """
        mwApp = self.getMwApp()
        apache_config = self.pw.apache_config(mwApp)
        debug = self.debug
        #debug = True
        if debug:
            print(apache_config)
        self.assertTrue("ServerName test.bitplan.com" in apache_config)

    def test_create(self):
        """
        test creating a wiki
        """
        # remember the docker application
        self.mwApp = self.startMwApp()

    def test_logo(self):
        """
        test the logo
        """
        return
        argv = [
            "--container_name",
            "logotest",
            "--basePort",
            "11001",
            "--sqlBasePort",
            "11002",
        ]
        mwApp = self.getMwApp(argv=argv, forceRebuild=True)
        ls_path = f"{mwApp.dockerPath}/Localsettings.php"
        print(f"checking {ls_path} to exist for {mwApp.config.as_dict()}")
        self.assertTrue(os.path.isfile(ls_path))
        with open(ls_path) as ls_file:
            ls_text = ls_file.read()
            self.assertTrue("Profiwikiicon.png" in ls_text)
        # looking on page itself is version dependent and
        # image is hidden in css /background
        # url=mwApp.config.url
        # main_page_url=f"{url}/index.php/Main_Page"
        # web_scrape=WebScrape()
        # soup=web_scrape.getSoup(main_page_url,showHtml=debug)
        #    self.mwApp=self.startMwApp()
        pass

    def test_install_plantuml(self):
        """
        test installing plantuml

        takes ~108 secs on laptop
        """
        if self.mwApp is None:
            self.mwApp = self.startMwApp()
        pmw, _pdb = self.pw.getProfiWikiContainers(self.mwApp)
        pmw.install_plantuml()
        pass

    def test_install_fontawesome(self):
        """
        test installing font awesome

        """
        if self.mwApp is None:
            self.mwApp = self.startMwApp()
        pmw, _pdb = self.pw.getProfiWikiContainers(self.mwApp)
        pmw.install_fontawesome()

    def test_killremove(self):
        """
        test kill and remove a container
        """
        if self.mwApp is None:
            self.mwApp = self.startMwApp()
        pmw, pdb = self.pw.getProfiWikiContainers(self.mwApp)
        pmw.killremove()
        pdb.killremove()
