'''
Created on 2023-04-01

@author: wf
'''
from argparse import ArgumentParser #Namespace
from argparse import RawDescriptionHelpFormatter
from profiwiki.version import Version
from profiwiki.profiwiki_core import ProfiWiki
#from pathlib import Path
import sys
import traceback
import webbrowser
from mwdocker.config import MwClusterConfig

class ProfiWikiCmd():
    """
    ProfiWiki command line
    """
    
    def get_arg_parser(self,config:MwClusterConfig, description: str, version_msg: str) -> ArgumentParser:
        """
        Setup command line argument parser
        
        Args:
            config(MwClusterConfig): the mediawiki cluster configuration
            description(str): the description
            version_msg(str): the version message
            
        Returns:
            ArgumentParser: the argument parser
        """
        #script_path=Path(__file__)
        parser = ArgumentParser(description=description, formatter_class=RawDescriptionHelpFormatter)
        config.addArgs(parser)
        parser.add_argument("--about", help="show about info [default: %(default)s]", action="store_true")
        parser.add_argument("--apache",help="generate apache configuration",action="store_true")
        parser.add_argument("--all",help="do all necessary steps for a full setup",action="store_true")
        parser.add_argument("--bash",help="bash into container",action="store_true")
        parser.add_argument("--create",action="store_true",help="create the wiki") 
        parser.add_argument("--check",action="store_true",help="check the wiki")  
        parser.add_argument("--update",action="store_true",help="start the update script -e.g. to fix SMW key")  
        parser.add_argument("--cron",action="store_true",help="start cron service")        
        parser.add_argument("--down", action="store_true", help="shutdown the wiki [default: %(default)s]")
        parser.add_argument("--patch", action="store_true", help="apply LocalSettings.php patches [default: %(default)s]")
        parser.add_argument("--list",action="store_true",help="list the available profi wikis [default: %(default)s]")
        parser.add_argument("-fa", "--fontawesome",   action="store_true", help="install fontawesome")
        parser.add_argument("-wuc", "--wikiuser_check",   action="store_true", help="check wikiuser")
        parser.add_argument("-pu", "--plantuml",   action="store_true", help="install plantuml")
        parser.add_argument("-i", "--info", help="show system info", action="store_true")
        parser.add_argument("-V", "--version", action='version', version=version_msg)
        # debug args
        parser.add_argument('--debugServer', help="remote debug Server")
        parser.add_argument('--debugPort', type=int, help="remote debug Port", default=5678)
        parser.add_argument('--debugPathMapping', nargs='+',
                            help="remote debug Server path mapping - needs two arguments 1st: remotePath 2nd: local Path")
        return parser

    def optional_debug(self, args):
        """
        start the remote debugger if the arguments specify so

        Args:
            args: The command line arguments
        """
        if args.debugServer:
            import pydevd
            import pydevd_file_utils
            print(args.debugPathMapping, flush=True)
            if args.debugPathMapping:
                if len(args.debugPathMapping) == 2:
                    remotePath = args.debugPathMapping[0]  # path on the remote debugger side
                    localPath = args.debugPathMapping[1]  # path on the local machine where the code runs
                    MY_PATHS_FROM_ECLIPSE_TO_PYTHON = [(remotePath, localPath), ]
                    pydevd_file_utils.setup_client_server_paths(
                        MY_PATHS_FROM_ECLIPSE_TO_PYTHON)  # os.environ["PATHS_FROM_ECLIPSE_TO_PYTHON"]='[["%s", "%s"]]' % (remotePath,localPath)  # print("trying to debug with PATHS_FROM_ECLIPSE_TO_PYTHON=%s" % os.environ["PATHS_FROM_ECLIPSE_TO_PYTHON"]);

            pydevd.settrace(args.debugServer, port=args.debugPort, stdoutToServer=True, stderrToServer=True)
            print("command line args are: %s" % str(sys.argv))
            pass
    
def main(argv=None):  # IGNORE:C0111
    """main program."""

    if argv is None:
        argv = sys.argv[1:]

    program_name = "profiwiki"
    program_version = f"v{Version.version}"
    program_build_date = str(Version.date)
    program_version_message = f'{program_name} ({program_version},{program_build_date})'

    args = None
    try:
        pw=ProfiWiki()
        pw_cmd = ProfiWikiCmd()
        parser = pw_cmd.get_arg_parser(
            config=pw.config,
            description=Version.license, 
            version_msg=program_version_message)
        args = parser.parse_args(argv)
        if len(argv) < 1:
            parser.print_usage()
            sys.exit(1)
        if args.about:
            print(program_version_message)
            print(f"see {Version.doc_url}")
            webbrowser.open(Version.doc_url)
        pw_cmd.optional_debug(args)
        if args.info:
            info=pw.system_info()
            print(info)
        pw.work(args)

    except KeyboardInterrupt:
        ###
        # handle keyboard interrupt
        # ###
        return 1
    except Exception as e:
        if DEBUG:
            raise e
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if args is None:
            print("args could not be parsed")
        elif args.debug:
            print(traceback.format_exc())
        return 2

DEBUG = 1
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())