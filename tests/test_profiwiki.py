'''
Created on 2023-04-01

@author: wf
'''
from tests.basetest import Basetest
from profiwiki.profiwiki_core import ProfiWiki
import json
from argparse import ArgumentParser

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
        self.pw=ProfiWiki(prefix="pwt",port=9142)
        self.mwApp=None
        
    def testConfig(self):
        """
        test the config
        """
        config_dict=self.pw.config.as_dict()
        debug=self.debug
        if debug:
            print(json.dumps(config_dict,indent=2))
        self.assertEqual("pwt",self.pw.config.prefix)
        
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
    
    def startMwApp(self):
        argv=["--prefix","pwt1","--basePort","11000","--sqlBasePort","11001"]
        pw=self.getProfiWiki(argv)
        forceRebuild=True
        pw.config.forceRebuild=forceRebuild
        mwApp=pw.getMwApp()
        mwApp.down(forceRebuild=forceRebuild)
        mwApp.start(forceRebuild=forceRebuild,withInitDB=True)
        mwApp.check()
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
        