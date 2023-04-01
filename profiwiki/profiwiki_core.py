'''
Created on 2023-04-01

@author: wf
'''
import platform
import os
from mwdocker.mwcluster import MediaWikiCluster

class ProfiWiki():
    """
    ProfiWiki
    """
    
    def __init__(self,args=None,verbose:bool=True,debug:bool=False):
        """
        constructor
        """
        self.os_name=platform.system()
        self.os_uname=os.uname()
        self.os_release=platform.release()
        self.args=args
        self.debug=debug
        self.verbose=verbose
        if args:
            self.debug=debug or self.args.debug
            if args.quiet:
                self.verbose=False
        
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
    
    def work(self):
        """
        work as instructed by the arguments
        """
        if self.args.create:
            self.create(self.args.prefix,self.args.port)
            
    def create(self,prefix,port,forceRebuild:bool=False):
        """
        create a mediawiki
        """
        mw_version="1.39.2"
        container_name=f"{prefix}-{port}"
        if self.verbose:
            print(f"creating ProfiWiki {prefix} using port {port}")
            versions=[mw_version]
            user=user=MediaWikiCluster.defaultUser
            password=MediaWikiCluster.defaultPassword
            extensionNameList=["Admin Links","Diagrams","Header Tabs","ImageMap","MagicNoCache","Maps9",
                               "Mermaid","MsUpload","Nuke","Page Forms","ParserFunctions","PDFEmbed","Renameuser",
                               "Replace Text","Semantic Result Formats","SyntaxHighlight","Variables"]
            mwCluster=MediaWikiCluster(versions=versions,user=user,password=password,container_name=container_name,extensionNameList=extensionNameList)
            mwCluster.createApps()
            mwCluster.start(forceRebuild=forceRebuild)
    