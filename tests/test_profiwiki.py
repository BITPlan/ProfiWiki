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
        forceRebuild=True
        pw.create(prefix="pw",port=9142,forceRebuild=forceRebuild)
        pw.check(prefix="pw",port=9142)
        
    def test_install_plantuml(self):
        """
        test installing plantuml
        """
        pw=ProfiWiki(debug=True)
        mwCluster=pw.getMwCluster(prefix="pw", port=9142)
        pmw,_pdb=pw.getProfiWikiContainers(mwCluster)
        pmw.install_plantuml()
        pass
        