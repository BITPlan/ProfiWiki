'''
Created on 2023-04-01

@author: wf
'''
import platform
import os
class ProfiWiki():
    """
    ProfiWiki
    """
    
    def __init__(self):
        """
        constructor
        """
        self.os_name=platform.system()
        self.os_uname=os.uname()
        self.os_release=platform.release()
        
    def system_info(self)->str:
        """
        collect system information
        """
        info=f"""os: {self.os_name}"""
        if "Darwin" in info:
            release,_version,_machine=platform.mac_ver()
            info+=f" MacOS {release}"
        else:
            info+=f"{self.os_release}"
        return info
        