'''
Created on 2023-04-01

@author: wf
'''
from tests.basetest import Basetest
from profiwiki.profiwiki_core import ProfiWiki

class TestProfiWiki(Basetest):
    """
    test ProfiWiki
    """
    
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # change the port for the testwiki to not spoil a wiki on the default port
        self.pw=ProfiWiki(self.debug)
        self.prefix="pwt"
        self.port=9142
        
    def getMwCluster(self):
        mwCluster=self.pw.getMwCluster(prefix=self.prefix,port=self.port)
        return mwCluster
    
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
        mwCluster=self.getMwCluster()
        forceRebuild=True
        self.pw.create(mwCluster,forceRebuild=forceRebuild)
        self.pw.check(mwCluster)
        
    def test_install_plantuml(self):
        """
        test installing plantuml
        """
        mwCluster=self.getMwCluster()
        pmw,_pdb=self.pw.getProfiWikiContainers(mwCluster)
        pmw.install_plantuml()
        pass
    
    def test_install_fontawesome(self):
        """
        test installing font awesome
        """
        mwCluster=self.getMwCluster()
        pmw,_pdb=self.pw.getProfiWikiContainers(mwCluster)
        pmw.install_fontawesome()
    
    def test_killremove(self):
        """
        test kill and remove a container
        """
        mwCluster=self.getMwCluster()
        pmw,pdb=self.pw.getProfiWikiContainers(mwCluster)
        pmw.killremove()
        pdb.killremove()


    def test_random_password(self):
        """
        test the random password generation
        """
        for length,chars in [(11,15),(13,18),(15,20)]:
            rp=self.pw.random_password(length)
            debug=self.debug
            if debug:
                print(f"{length} bytes:{len(rp)} chars:{rp}")
            self.assertEqual(chars,len(rp))    
        