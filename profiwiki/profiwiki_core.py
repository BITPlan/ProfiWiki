'''
Created on 2023-04-01

@author: wf
'''
import platform
import os
from mwdocker.mwcluster import MediaWikiCluster
from profiwiki.docker import ProfiWikiContainer

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
        
    def getMwCluster(self,prefix,port): 
        """
        get the mediawiki cluster
        """   
        self.mw_version="1.39.2"
        self.prefix=prefix
        self.port=port
        self.versions=[self.mw_version]
        self.user=MediaWikiCluster.defaultUser
        self.password=MediaWikiCluster.defaultPassword
        self.extensionNameList=["Admin Links","Diagrams","Header Tabs","ImageMap","MagicNoCache","Maps9",
                               "Mermaid","MsUpload","Nuke","Page Forms","ParserFunctions","PDFEmbed","Renameuser",
                               "Replace Text","Semantic Result Formats","SyntaxHighlight","Variables"]
        self.smwVersion="4.1.0"
        self.container_name=f"{prefix}-{port}"
        if self.verbose:
            os_path=os.environ["PATH"]
            paths=["/usr/local/bin"]
            for path in paths:
                if not path in os_path:
                    os.environ["PATH"]=f"{os_path}{os.pathsep}{path}"
            if self.debug:
                print(f"""modified PATH from {os_path} to \n{os.environ["PATH"]}""")
            print(f"creating ProfiWiki {prefix} using port {port}")
        mwCluster=MediaWikiCluster(versions=self.versions,
            user=self.user,
            password=self.password,
            container_name=self.container_name,
            extensionNameList=self.extensionNameList,
            basePort=self.port,
            smwVersion=self.smwVersion)
        mwCluster.createApps()
        return mwCluster
    
    def getProfiWikiContainers(self,mwCluster):
        mwApp=mwCluster.apps[self.mw_version]
        mw,db=mwApp.getContainers()
        pmw=ProfiWikiContainer(mw)
        pdb=ProfiWikiContainer(db)
        return pmw,pdb
        
    def check(self,prefix,port):
        """
        check
        """
        mwCluster=self.getMwCluster(prefix, port)
        mwCluster.check()
            
    def create(self,prefix,port,forceRebuild:bool=False):
        """
        create a mediawiki
        """
        mwCluster=self.getMwCluster(prefix, port)
        mwCluster.start(forceRebuild=forceRebuild)
    