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
    
    def test_system(self):
        """
        test system pre requisites
        """
        pw=ProfiWiki()
        info=pw.system_info()
        debug=True
        if debug:
            print(info)
            
    def test_create(self):
        """
        test creating a wiki
        """
        pw=ProfiWiki(debug=True)
        mwCluster=pw.getMwCluster(prefix="pw",port=9142)
        forceRebuild=True
        pw.create(mwCluster,forceRebuild=forceRebuild)
        pw.check(mwCluster)
        
    def test_install_plantuml(self):
        """
        test installing plantuml
        """
        pw=ProfiWiki(debug=True)
        mwCluster=pw.getMwCluster(prefix="pw", port=9142)
        pmw,_pdb=pw.getProfiWikiContainers(mwCluster)
        pmw.install_plantuml()
        pass
    
    def test_install_fontawesome(self):
        """
        test installing font awesome
        """
        pw=ProfiWiki(debug=True)
        mwCluster=pw.getMwCluster(prefix="pw", port=9142)
        pmw,_pdb=pw.getProfiWikiContainers(mwCluster)
        pmw.install_fontawesome()
    
    def test_killremove(self):
        pw=ProfiWiki(debug=True)
        mwCluster=pw.getMwCluster(prefix="pw", port=9142)
        pmw,pdb=pw.getProfiWikiContainers(mwCluster)
        pmw.killremove()
        pdb.killremove()


    def test_random_password(self):
        """
        test the random password generation
        """
        pw=ProfiWiki()
        rp=pw.random_password(15)
        debug=True
        if debug:
            print(rp)
        self.assertEqual(15,len(rp))    
        