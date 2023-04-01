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
        #pw.create(prefix="pw",port=9142)
        