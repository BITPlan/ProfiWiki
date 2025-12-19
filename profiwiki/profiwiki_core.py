"""
Created on 2023-04-01

@author: wf
"""

import datetime
import json
import os
import platform
import tempfile

from mwdocker.config import MwClusterConfig
from mwdocker.docker import DockerApplication
from mwdocker.mwcluster import MediaWikiCluster
from wikibot3rd.wikiuser import WikiUser

from profiwiki.pw_container import ProfiWikiContainer
from profiwiki.patch import Patch


class ProfiWiki:
    """
    ProfiWiki
    """

    def __init__(
        self,
        prefix: str = "pw",
        smw_version="5.0.2",
        mw_version="1.39.17",
        port: int = 9079,
    ):
        """
        constructor
        """
        self.os_name = platform.system()
        self.os_uname = os.uname()
        self.os_release = platform.release()
        self.args = None
        self.config = MwClusterConfig()
        self.config.smw_version = smw_version
        self.config.random_password = False
        self.config.lenient = True
        self.config.prefix = prefix
        self.config.base_port = port
        self.config.sql_port = port - 1
        self.config.port = port
        self.config.versions = [mw_version]
        self.config.version = mw_version
        self.config.container_base_name = "pw"
        self.config.extensionNameList = [
            "Admin Links",
            "Diagrams",
            # "Graph", removed 2025-09-30
            "Header Tabs",
            "ImageMap",
            "ImageLink",
            "MagicNoCache",
            "Maps11",
            "Mermaid",
            "MsUpload",
            "Nuke",
            "Page Forms",
            "ParserFunctions",
            "PDFEmbed",
            "Renameuser",
            "Replace Text",
            #"Semantic Result Formats", Version4
            "SRF5",
            "Scribunto",
            "SyntaxHighlight",
            "Variables",
            "UserFunctions",
            "YouTube",
        ]
        self.config.logo = "https://wiki.bitplan.com/images/wiki/thumb/6/63/Profiwikiicon.png/96px-Profiwikiicon.png"
        self.config.__post_init__()
        self.mwCluster = None
        pass

    def system_info(self) -> str:
        """
        collect system information
        """
        info = f"""os: {self.os_name}"""
        if "Darwin" in info:
            release, _version, _machine = platform.mac_ver()
            info += f" MacOS {release}"
        else:
            info += f"{self.os_release}"
        return info

    def work(self, args):
        """
        work as instructed by the arguments

        Args:
            args(Namespace): the command line arguments
        """
        self.args = args
        self.config.fromArgs(args)
        # ProfiWiki specific configuration entries
        self.config.memcached = args.memcached
        # use bind mount if we are in family mode
        if self.args.family:
            self.config.bind_mount=True
        if len(self.config.versions) == 1:
            self.config.version = self.config.versions[0]

        # make sure the wikiId is set from the container base name
        config_path = self.config.get_config_path()
        if os.path.isfile(config_path) and not self.config.forceRebuild:
            # reload the previous configuration e.g. based on container_name only
            previous_config = self.config.load(config_path)
            if self.config.verbose:
                print(f"ProfiWiki with previous configuration from {config_path}...")
            self.config = previous_config
        self.config.wikiId = self.config.container_base_name
        if args.bash:
            cmd = f"docker exec -it {self.config.container_base_name}-mw /bin/bash"
            print(cmd)
            return
        mwApp = self.getMwApp(withGenerate=self.config.forceRebuild)
        if self.config.verbose:
            print(
                f"ProfiWiki {mwApp.config.container_base_name} using port {mwApp.config.port} sqlport {mwApp.config.sql_port}"
            )
        if args.force_user:
            mwApp.createWikiUser(store=True)
        if args.all:
            image_name = f"profiwiki:{mwApp.config.shortVersion}"
            image=ProfiWikiContainer.get_image(image_name)
            if image:
                # we could use the image here to speed up things
                pass
            self.create(mwApp,self.config.forceRebuild)
            pmw, _pdb = self.getProfiWikiContainers(mwApp)
            pmw.install_fontawesome()
            pmw.install_plantuml()
            pmw.commit(tag=image_name)
            mwApp.execute("/scripts/setup-mediawiki.sh","--all")
            self.patch(pmw)
        if args.wikiuser_check:
            self.check_wikiuser(mwApp)
        if args.apache:
            apache_config = self.apache_config(mwApp)
            print(apache_config)
        if args.create:
            self.create(mwApp, self.config.forceRebuild)
        if args.check:
            self.check(mwApp)
        if args.down:
            self.down(mwApp, self.config.forceRebuild)
        if args.list:
            self.list(mwApp)
        if args.plantuml or args.fontawesome or args.cron or args.patch:
            pmw, _pdb = self.getProfiWikiContainers(mwApp)
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

    def getMwCluster(self, withGenerate: bool = True) -> MediaWikiCluster:
        """
        get a mediawiki Cluster for my configuration

        Args:
            withGenerate(bool): if True regenerate the configuration files

        Returns:
            MediaWikiCluster: the MediaWiki Cluser
        """
        if self.mwCluster is not None:
            return self.mwCluster
        mwCluster = MediaWikiCluster(config=self.config)
        # make sure docker is in path
        mwCluster.checkDocker()
        # generate
        mwCluster.createApps(withGenerate=withGenerate)
        self.mwCluster = mwCluster
        return mwCluster

    def getMwApp(self, withGenerate: bool = True):
        """
        get my mediawiki Docker application
        """
        mwCluster = self.getMwCluster(withGenerate)
        if not self.config.version in mwCluster.apps:
            raise Exception(
                f"Mediawiki version {self.config.version} missing {mwCluster.apps.keys()}"
            )
        mwApp = mwCluster.apps[self.config.version]
        return mwApp

    def getProfiWikiContainers(self, mwApp: DockerApplication):
        """
        get the two containers - for mediawiki and the database

        Args:
            mwApp(DockerApplication): the MediaWiki Docker Application

        Returns:
            Tuple(ProfiWikiContainer,ProfiWikiContainer): MediaWiki, Database
        """
        mw, db = mwApp.getContainers()
        pmw = ProfiWikiContainer(mw)
        pdb = ProfiWikiContainer(db)
        return pmw, pdb

    def add_compose_service(self, mwApp: DockerApplication, service_key: str, service_yaml: str):
        """
        add a service to the docker compose file

        Args:
            mwApp(DockerApplication): the mediawiki application
            service_key(str): the key of the service e.g. memcached
            service_yaml(str): the yaml definition of the service (must start with indentation)
        """
        compose_path = f"{mwApp.dockerPath}/docker-compose.yml"
        with open(compose_path, "r") as f:
            content = f.read()

        # Idempotency check to ensure we don't add it twice
        if f"{service_key}:" not in content:
            if self.config.verbose:
                print(f"Adding {service_key} service to {compose_path}")
            with open(compose_path, "a") as f:
                f.write(service_yaml)

    def add_memcached(self, mwApp: DockerApplication):
        """
        add memcached to the docker compose file

        Args:
            mwApp(DockerApplication): the mediawiki application
        """
        memcached_service = """
  memcached:
    image: memcached:alpine
    restart: always"""
        self.add_compose_service(mwApp, "memcached", memcached_service)


    def patch(self, pwc: ProfiWikiContainer):
        """
        apply profi wiki patches to the given ProfiWikiContainer
        """
        if not pwc.dc:
            raise ("no container to apply patch")
        ls_path = "/var/www/html/LocalSettings.php"
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        with tempfile.NamedTemporaryFile(
            mode="w", prefix="LocalSettings_", suffix=".php"
        ) as ls_file:
            pwc.log_action(f"patching {ls_file.name}")
            pwc.dc.container.copy_from(ls_path, ls_file.name)
            patch = Patch(file_path=ls_file.name)
            lines = f"""// modified by profiwiki at {timestamp}
// use WikiEditor e.g. for MsUpload
wfLoadExtension( 'WikiEditor' );
# make this an intranet - comment out if you want this to be a public wiki
# The following permissions were set based on your choice in the installer
$wgGroupPermissions['*']['createaccount'] = false;
$wgGroupPermissions['*']['edit'] = false;
$wgGroupPermissions['*']['read'] = false;
# Allow properties in Templates
$smwgNamespacesWithSemanticLinks[NS_TEMPLATE] = true;
# WF 2015-01-20
# allow string functions - needed for Template:Link
$wgPFEnableStringFunctions=true;
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
// allow user functions in main mediawiki space
$wgUFAllowedNamespaces[NS_MAIN] = true;
# increase query limit
$smwgQMaxLimit = 20000;
//Default width for the PDF object container.
$wgPdfEmbed['width'] = 800;
//Default height for the PDF object container.
$wgPdfEmbed['height'] = 1090;
//Allow user the usage of the tag
$wgGroupPermissions['*']['embed_pdf'] = true;
// config parameters for MsUpload
// https://www.mediawiki.org/wiki/Extension:MsUpload
$wgMSU_useDragDrop = true; // Should the drag & drop area be shown? (Not set by default)
$wgMSU_showAutoCat = true; // Files uploaded while editing a category page will be added to that category
$wgMSU_checkAutoCat = true; // Whether the checkbox for adding a category to a page is checked by default
$wgMSU_useMsLinks = false; // Insert links in Extension:MsLinks style?
$wgMSU_confirmReplace = true; // Show the "Replace file?" checkbox
$wgMSU_imgParams = '400px'; // Default image parameters, for example "thumb|200px"
$wgMSU_uploadsize = '100mb'; // Max upload size through MsUpload
// general parameters for MsUpload
$wgEnableWriteAPI = true; // Enable the API
$wgEnableUploads = true; // Enable uploads
$wgAllowJavaUploads = true; // Solves problem with Office 2007 and newer files (docx, xlsx, etc.)
$wgGroupPermissions['user']['upload'] = true; // Allow regular users to upload files
# add more file upload options
$wgGroupPermissions['user']['upload_by_url'] = true;
$wgAllowCopyUploads = true;
$wgCopyUploadsFromSpecialUpload = true;
# http://www.mediawiki.org/wiki/Manual:Configuring_file_uploads/de
$wgFileExtensions = array_merge($wgFileExtensions, array('doc', 'gcode',
'gpx','htm','html','jscad','jpg','pdf','ppt','docx', 'docxm','xlsx','xlsm','mp3','mp4','odp','otp','pptx', 'pptm','reqif','reqifz','rtf','rythm'
,'scad','sh','stl','svg','vcf','vim','uew','xls','xml','zip'));
# allow html
$wgVerifyMimeType=false;
# disable upload script checks ...
$wgDisableUploadScriptChecks = true;
"""
            # memcached configuration lines
            if getattr(self.config, "memcached", False):
                lines += """# Memcached config
$wgMainCacheType = CACHE_MEMCACHED;
$wgParserCacheType = CACHE_MEMCACHED;
$wgMessageCacheType = CACHE_MEMCACHED;
$wgSessionCacheType = CACHE_MEMCACHED;
$wgMemCachedServers = [ 'memcached:11211' ];
$wgSessionsInObjectCache = true;
"""
            patch.add_text(lines)
            patch.save()
            pwc.dc.container.copy_to(ls_file.name, ls_path)

    def check(self, mwApp):
        """
        check
        """
        mwApp.check()

    def create(self, mwApp,forceRebuild: bool = False):
        """
        create a profiwiki mediawiki
        """
        mwApp.start(forceRebuild=forceRebuild)

    def down(self, mwApp, forceRebuild: bool = False):
        """
        shut down the profiwiki base mediawiki
        """
        mwApp.down(forceRebuild=forceRebuild)

    def list(self, mwApp):
        """
        list the profi wikis
        """
        print(json.dumps(mwApp.config.as_dict(), indent=2))
        pass

    def check_wikiuser(self, mwApp: DockerApplication):
        """ """
        print(f"Checking WikiUser ... for {mwApp.config.container_base_name}")
        wikiUsers = WikiUser.getWikiUsers(lenient=True)
        if not mwApp.config.wikiId:
            print("no WikiId configured")
            return
        if not mwApp.config.wikiId in wikiUsers:
            print(f"no wikiUser for wikiId {mwApp.config.wikiId} found")
            return
        wikiUser = wikiUsers[mwApp.config.wikiId]
        if mwApp.config.password != wikiUser.getPassword():
            print(f"configured password is different then {mwApp.config.wikiId}")
        else:
            print(
                f"wikiUser for wikiId {mwApp.config.wikiId} is available and password as configured"
            )
        pass

    def apache_config(self, mwApp: DockerApplication) -> str:
        """
        get the apache configuration for the given mediawiki Docker application

        Args:
            mwApp(DockerApplication): the docker application to generate the configuration for
        """
        config = mwApp.config
        iso_timestamp = datetime.datetime.now().isoformat()
        server_name = f"{self.args.apache}"
        header_comment = f"""# Apache Configuration for {server_name}
# Generated by ProfiWiki at {iso_timestamp}
"""
        apache_config = f"""{header_comment}<VirtualHost *:443>
    ServerName {server_name}
    ServerAdmin webmaster@{config.host}

    ErrorLog ${{APACHE_LOG_DIR}}/{config.container_base_name}_error.log
    CustomLog ${{APACHE_LOG_DIR}}/{config.container_base_name}_access.log combined

    ProxyPass / http://localhost:{config.port}/
    ProxyPassReverse / http://localhost:{config.port}/
</VirtualHost>
<VirtualHost *:80>
    ServerName {server_name}
    Redirect permanent / https://{server_name}/
</VirtualHost>
"""
        return apache_config
