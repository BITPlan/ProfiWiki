'''
Created on 2023-04-01

@author: wf
'''
import platform
import os
import secrets
from mwdocker.mwcluster import MediaWikiCluster
from profiwiki.docker import ProfiWikiContainer
from wikibot3rd.wikiuser import WikiUser

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
        self.password=MediaWikiCluster.defaultPassword
        self.wikiUser=None
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
        mwCluster=self.getMwCluster(self.args.prefix,port=self.args.port,sqlPort=self.args.sqlPort)
        if self.args.randompassword:
            self.password=self.random_password()
            self.wikiUser=self.createOrModifyWikiUser(force_overwrite=self.args.forceuser)
        if self.args.wikiuser and not self.wikiUser:
            self.createOrModifyWikiUser(force_overwrite=self.args.forceuser)
        if self.args.all:
            if not self.wikiUser:
                self.wikiUser=self.createOrModifyWikiUser()
            self.create(mwCluster, self.args.forcerebuild)
            pmw,_pdb=self.getProfiWikiContainers(mwCluster)
            pmw.install_fontawesome()
            pmw.install_plantuml()
            pmw.start_cron()
        if self.args.create:
            self.create(mwCluster, self.args.forcerebuild)
        if self.args.plantuml:
            pmw,_pdb=self.getProfiWikiContainers(mwCluster)
            pmw.install_plantuml()
        if self.args.fontawesome:
            pmw,_pdb=self.getProfiWikiContainers(mwCluster)
            pmw.install_fontawesome()
        if self.args.cron:
            pmw,_pdb=self.getProfiWikiContainers(mwCluster)
            pmw.start_cron()
        if self.args.killremove:
            pmw,pdb=self.getProfiWikiContainers(mwCluster)
            pmw.killremove()
            pdb.killremove()
            
    def createOrModifyWikiUser(self,force_overwrite:bool=False)->WikiUser:
        """
        create or modify the WikiUser for this profiwiki
        
        Args:
            force_overwrite(bool): if True overwrite the wikuser info
        """
        wikiUsers=WikiUser.getWikiUsers(lenient=True)
        if self.wiki_id in wikiUsers and not force_overwrite:
            wikiUser=wikiUsers[self.wiki_id]          
            if self.password != wikiUser.getPassword():
                raise Exception(f"wikiUser for wiki {self.wiki_id} already exists but with different password")
            pass
        else:
            userDict = {
                "wikiId": self.wiki_id, 
                "email": "noreply@nouser.com", 
                "url": "https://cr.bitplan.com",
                "scriptPath": "", 
                "version": f"MediaWiki {self.mw_version}",
                "user": "Sysop",
                "password": f"{self.password}"
            }
            wikiUser=WikiUser.ofDict(userDict,encrypted=False)
            wikiUser.save()
        return wikiUser

    def random_password(self,length:int = 13)->str:
        """
        create a random password

        Args:
            length(int): the length of the password

        Returns:
            str:a random password with the given length
        """
        return secrets.token_urlsafe(length)
        
    def getMwCluster(self,prefix,port,sqlPort:int=None): 
        """
        get the mediawiki cluster
        """   
        self.mw_version="1.39.3"
        self.prefix=prefix
        self.port=port
        if sqlPort is None:
            sqlPort=port+264 # 9306 for default 9042 port
        self.sqlPort=sqlPort
        self.versions=[self.mw_version]
        self.user=MediaWikiCluster.defaultUser
        self.extensionNameList=["Admin Links","Diagrams","Header Tabs","ImageMap","MagicNoCache","Maps9",
                               "Mermaid","MsUpload","Nuke","Page Forms","ParserFunctions","PDFEmbed","Renameuser",
                               "Replace Text","Semantic Result Formats","SyntaxHighlight","Variables"]
        self.smwVersion="4.1.0"
        self.wiki_id=f"{prefix}-{port}"
        self.container_name=self.wiki_id
        if self.verbose:
            os_path=os.environ["PATH"]
            paths=["/usr/local/bin"]
            for path in paths:
                if not path in os_path:
                    os.environ["PATH"]=f"{os_path}{os.pathsep}{path}"
            if self.debug:
                print(f"""modified PATH from {os_path} to \n{os.environ["PATH"]}""")
            print(f"ProfiWiki {prefix} using port {port}")
            
        mwCluster=MediaWikiCluster(versions=self.versions,
            user=self.user,
            password=self.password,
            container_name=self.container_name,
            extensionNameList=self.extensionNameList,
            basePort=self.port,
            sqlPort=self.sqlPort,
            smwVersion=self.smwVersion)
        # generate
        mwCluster.createApps()
        return mwCluster
    
    def getProfiWikiContainers(self,mwCluster):
        """
        get the two containers - for mediawiki and the database
        """
        mwApp=mwCluster.apps[self.mw_version]
        mw,db=mwApp.getContainers()
        pmw=ProfiWikiContainer(mw)
        pdb=ProfiWikiContainer(db)
        return pmw,pdb
        
    def check(self,mwCluster):
        """
        check
        """
        mwCluster.check()
            
    def create(self,mwCluster,forceRebuild:bool=False):
        """
        create a mediawiki
        """
        mwCluster.start(forceRebuild=forceRebuild)
        
    