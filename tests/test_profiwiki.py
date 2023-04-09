'''
Created on 2023-04-01

@author: wf
'''
from tests.basetest import Basetest
from profiwiki.profiwiki_core import ProfiWiki
import json
import os
from argparse import ArgumentParser
#from mwdocker.webscrape import WebScrape

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
        self.pw=ProfiWiki(prefix="pwt1",port=11000)
        self.mwApp=None
        self.argv=["--prefix","pwt1","--basePort","11000","--sqlBasePort","11001"]
        
    def testConfig(self):
        """
        test the config
        """
        config_dict=self.pw.config.as_dict()
        debug=self.debug
        if debug:
            print(json.dumps(config_dict,indent=2))
        self.assertEqual("pwt1",self.pw.config.prefix)
        
    def getProfiWiki(self,argv=[]):
        """
        get a profiwiki for the given command line arguments
        """
        parser = ArgumentParser()
        pw=ProfiWiki()
        pw.config.addArgs(parser)
        args = parser.parse_args(argv)
        pw.config.fromArgs(args)
        return pw
    
    def getMwApp(self,forceRebuild:bool=False):
        """
        get the mediaWikiApp
        """
        self.pw=self.getProfiWiki(self.argv)
        self.pw.config.forceRebuild=forceRebuild
        mwApp=self.pw.getMwApp(withGenerate=forceRebuild)
        return mwApp
    
    def doStartMwApp(self,mwApp,forceRebuild:bool=True):
        """
        start MW App
        """
        if forceRebuild:
            mwApp.down(forceRebuild=forceRebuild)
        mwApp.start(forceRebuild=forceRebuild,withInitDB=forceRebuild)
        mwApp.check()
    
    def startMwApp(self):
        """
        start mediawiki application
        """
        forceRebuild=True
        mwApp=self.getMwApp(forceRebuild)
        self.doStartMwApp(mwApp)
        return mwApp
    
    def test_system(self):
        """
        test system pre requisites
        """
        info=self.pw.system_info()
        debug=True
        if debug:
            print(info)
            
    def test_create(self):
        """
        test creating a wiki
        """
        # remember the docker application
        self.mwApp=self.startMwApp()
        
    def test_logo(self):
        """
        test the logo
        """
        mwApp=self.getMwApp(forceRebuild=False)
        ls_path=f"{mwApp.dockerPath}/Localsettings.php"
        print (f"checking {ls_path} to exist for {mwApp.config.as_dict()}")
        self.assertTrue(os.path.isfile(ls_path))
        with open(ls_path) as ls_file:
            ls_text= ls_file.read()
            self.assertTrue("Profiwikiicon.png" in ls_text)
        # looking on page itself is version dependent and
        # image is hidden in css /background
        #url=mwApp.config.url
        #main_page_url=f"{url}/index.php/Main_Page"
        #web_scrape=WebScrape()
        #soup=web_scrape.getSoup(main_page_url,showHtml=debug)
        #    self.mwApp=self.startMwApp()
        pass
        
    def test_install_plantuml(self):
        """
        test installing plantuml
        
        takes ~108 secs on laptop
        """
        if self.mwApp is None:
            self.mwApp=self.startMwApp()
        pmw,_pdb=self.pw.getProfiWikiContainers(self.mwApp)
        pmw.install_plantuml()
        pass
    
    def test_install_fontawesome(self):
        """
        test installing font awesome
        
        """
        if self.mwApp is None:
            self.mwApp=self.startMwApp()
        pmw,_pdb=self.pw.getProfiWikiContainers(self.mwApp)
        pmw.install_fontawesome()
    
    def test_killremove(self):
        """
        test kill and remove a container
        """
        if self.mwApp is None:
            self.mwApp=self.startMwApp()
        pmw,pdb=self.pw.getProfiWikiContainers(self.mwApp)
        pmw.killremove()
        pdb.killremove()
        