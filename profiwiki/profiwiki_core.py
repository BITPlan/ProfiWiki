'''
Created on 2023-04-01

@author: wf
'''
import datetime
import json
import tempfile
import platform
import os
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.docker import DockerApplication
from profiwiki.docker import ProfiWikiContainer
from wikibot3rd.wikiuser import WikiUser
from mwdocker.config import MwClusterConfig
from profiwiki.patch import Patch

class ProfiWiki():
    """
    ProfiWiki
    """
    
    def __init__(self,prefix:str="pw",smw_version="4.1.1",mw_version="1.39.3",port:int=9079):
        """
        constructor
        """        
        self.os_name=platform.system()
        self.os_uname=os.uname()
        self.os_release=platform.release()
        self.args=None
        self.wikiUser=None
        self.config=MwClusterConfig()
        self.config.smwVersion=smw_version
        self.config.prefix=prefix
        self.config.basePort=port
        self.config.sqlPort=port-1
        self.config.port=port
        self.config.versions=[mw_version]
        self.config.container_base_name="pw"
        self.config.extensionNameList=["Admin Links","Diagrams","Header Tabs","ImageMap","ImageLink","MagicNoCache","Maps9",
                               "Mermaid","MsUpload","Nuke","Page Forms","ParserFunctions","PDFEmbed","Renameuser",
                               "Replace Text","Semantic Result Formats","SyntaxHighlight","Variables","UserFunctions"]
        self.config.logo="https://wiki.bitplan.com/images/wiki/thumb/6/63/Profiwikiicon.png/96px-Profiwikiicon.png"
        self.config.__post_init__()
        self.mwCluster=None
        pass
        
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
    
    def work(self,args):
        """
        work as instructed by the arguments
        
        Args:
            args(Namespace): the command line arguments
        """
        self.config.fromArgs(args)
        self.wiki_id=f"{self.config.container_base_name}"
        if args.bash:
            cmd=f"docker exec -it {self.config.container_base_name}-mw /bin/bash"
            print(cmd)
            return
        mwApp=self.getMwApp(withGenerate=args.forceRebuild)
        if self.config.verbose:
            print(f"ProfiWiki {mwApp.config.container_base_name} using port {mwApp.config.port} sqlport {mwApp.config.sqlPort}")
   
        if args.randompassword:
            mwApp.config.password=self.config.random_password()
            self.wikiUser=self.createOrModifyWikiUser(mwApp,force_overwrite=args.forceuser)
        if args.wikiuser and not self.wikiUser:
            self.createOrModifyWikiUser(mwApp,force_overwrite=args.forceuser)
        if args.all:
            if not self.wikiUser:
                self.wikiUser=self.createOrModifyWikiUser(mwApp,force_overwrite=args.forceuser)
            self.create(mwApp, args.forceRebuild)
            pmw,_pdb=self.getProfiWikiContainers(mwApp)
            pmw.install_fontawesome()
            pmw.install_plantuml()
            self.patch(pmw)
            self.update(mwApp)
            pmw.start_cron()
        if args.create:
            self.create(mwApp, args.forceRebuild)
        if args.check:
            self.check(mwApp)
        if args.down:
            self.down(mwApp,args.forceRebuild)
        if args.list:
            self.list(mwApp)
        if args.plantuml or args.fontawesome or args.cron or args.patch:
            pmw,_pdb=self.getProfiWikiContainers(mwApp)
            if args.plantuml:
                pmw.install_plantuml()
            if args.fontawesome:
                pmw.install_fontawesome()
            if args.cron:
                pmw.start_cron()
            if args.patch:
                self.patch(pmw)
        if args.update:
            self.update(mwApp)
            
    def createOrModifyWikiUser(self,mwApp,force_overwrite:bool=False)->WikiUser:
        """
        create or modify the WikiUser for this profiwiki
        
        Args:
            mwApp(DockerApplication): the mediawiki docker application
            force_overwrite(bool): if True overwrite the wikuser info
        """
        wikiUsers=WikiUser.getWikiUsers(lenient=True)
        if self.wiki_id in wikiUsers and not force_overwrite:
            wikiUser=wikiUsers[self.wiki_id]          
            if self.config.password != wikiUser.getPassword():
                raise Exception(f"wikiUser for wiki {self.wiki_id} already exists but with different password")
            pass
        else:
            wikiUser=mwApp.createWikiUser(self.wiki_id,store=True)
        return wikiUser
    
    def getMwCluster(self,withGenerate:bool=True)->MediaWikiCluster:
        """
        get a mediawiki Cluster for my configuration
        
        Args:
            withGenerate(bool): if True regenerate the configuration files
            
        Returns:
            MediaWikiCluster: the MediaWiki Cluser
        """
        if self.mwCluster is not None:
            return self.mwCluster
        mwCluster=MediaWikiCluster(config=self.config)
        # generate
        mwCluster.createApps(withGenerate=withGenerate)
        self.mwCluster=mwCluster
        return mwCluster
    
    def getMwApp(self,withGenerate:bool=True): 
        """
        get my mediawiki Docker application 
        """   
        mwCluster=self.getMwCluster(withGenerate)
        mwApp=mwCluster.apps[self.config.version]
        return mwApp
    
    def getProfiWikiContainers(self,mwApp:DockerApplication):
        """
        get the two containers - for mediawiki and the database
        
        Args:
            mwApp(DockerApplication): the MediaWiki Docker Application
            
        Returns:
            Tuple(ProfiWikiContainer,ProfiWikiContainer): MediaWiki, Database
        """
        mw,db=mwApp.getContainers()
        pmw=ProfiWikiContainer(mw)
        pdb=ProfiWikiContainer(db)
        return pmw,pdb
    
    def patch(self,pwc:ProfiWikiContainer):
        """
        apply profi wiki patches to the given ProfiWikiContainer
        """
        if not pwc.dc:
            raise("no container to apply patch")
        ls_path="/var/www/html/LocalSettings.php"
        timestamp=datetime.datetime.utcnow().strftime('%Y-%m-%d')
        with tempfile.NamedTemporaryFile(mode='w', prefix='LocalSettings_', suffix='.php') as ls_file:
            pwc.log_action(f"patching {ls_file.name}")
            pwc.dc.container.copy_from(ls_path,ls_file.name)
            patch=Patch(file_path=ls_file.name)
            lines=f"""// modified by profiwiki 
# make this an intranet - comment out if you want this to be a public wiki
# The following permissions were set based on your choice in the installer
$wgGroupPermissions['*']['createaccount'] = false;
$wgGroupPermissions['*']['edit'] = false;
$wgGroupPermissions['*']['read'] = false;
// allow raw HTML 
$wgRawHtml = true;
// allow images
$wgAllowImageTag=true;
// InstantCommons allows wiki to use images from https://commons.wikimedia.org
$wgUseInstantCommons = true;
// avoid showing (expected) deprecation warnings
error_reporting(E_ERROR | E_WARNING | E_PARSE | E_NOTICE);
# # add support for special properties
# see https://www.semantic-mediawiki.org/wiki/Help:$smwgPageSpecialProperties
# Modification date
$smwgPageSpecialProperties[] = '_MDAT';
# Creation date
$smwgPageSpecialProperties[] = '_CDAT';
# Is a new page
$smwgPageSpecialProperties[] = '_NEWP';
# Last editor is
$smwgPageSpecialProperties[] = '_LEDT';
# Media type
$smwgPageSpecialProperties[] = '_MEDIA';
# MIME type
$smwgPageSpecialProperties[] = '_MIME';
// https://www.mediawiki.org/wiki/Extension:UserFunctions
$wgUFEnabledPersonalDataFunctions = ['ip','nickname','realname','useremail','username',];
# increase query limit
$smwgQMaxLimit = 20000;
//Default width for the PDF object container.
$wgPdfEmbed['width'] = 800;
//Default height for the PDF object container.
$wgPdfEmbed['height'] = 1090;
//Allow user the usage of the tag 
$wgGroupPermissions['*']['embed_pdf'] = true;
"""
            patch.add_text(lines)
            patch.save()
            pwc.dc.container.copy_to(ls_file.name,ls_path)

    def update(self,mwApp):
        """
        run the update script
        """
        mwApp.execute("/root/update.sh")
        
    def check(self,mwApp):
        """
        check
        """
        mwApp.check()
            
    def create(self,mwApp,forceRebuild:bool=False):
        """
        create a profiwiki mediawiki
        """
        mwApp.start(forceRebuild=forceRebuild)
        
    def down(self,mwApp,forceRebuild:bool=False):
        """
        shut down the profiwiki base mediawiki
        """
        mwApp.down(forceRebuild=forceRebuild)
        
    def list(self,mwApp):
        """
        list the profi wikis
        """
        print (json.dumps(mwApp.config.as_dict(),indent=2))
        pass