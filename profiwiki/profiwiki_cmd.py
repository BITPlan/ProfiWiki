"""
Created on 2023-04-01

@author: wf
"""

# from pathlib import Path
import sys
from typing import List

from basemkit.base_cmd import BaseCmd
from profiwiki.profiwiki_core import ProfiWiki
from profiwiki.version import Version


class ProfiWikiCmd(BaseCmd):
    """
    ProfiWiki command line
    """

    def __init__(self, version: Version):
        super().__init__(version)
        self.pw = ProfiWiki()

    def add_arguments(self, parser):
        super().add_arguments(parser)
        self.pw.config.addArgs(parser)
        parser.add_argument(
            "--apache",
            help="generate apache configuration for the given server name",
        )
        parser.add_argument(
            "--all", help="do all necessary steps for a full setup", action="store_true"
        )
        parser.add_argument(
            "--anubis",
            action="store_true",
            help="add anubis support [default: %(default)s]",
        )
        parser.add_argument("--bash", help="bash into container", action="store_true")
        parser.add_argument("--create", action="store_true", help="create the wiki")
        parser.add_argument("--check", action="store_true", help="check the wiki")
        parser.add_argument("--cron", action="store_true", help="start cron service")
        parser.add_argument(
            "--down",
            action="store_true",
            help="shutdown the wiki [default: %(default)s]",
        )
        parser.add_argument(
            "--elastica",
            action="store_true",
            help="add elastica/cirrus search support [default: %(default)s]",
        )
        parser.add_argument(
            "-fa", "--fontawesome", action="store_true", help="install fontawesome"
        )
        parser.add_argument(
            "--family", action="store_true", help="support wiki family e.g. with bind mounts"
        )
        parser.add_argument(
            "-i", "--info", help="show system info", action="store_true"
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="list the available profi wikis [default: %(default)s]",
        )
        parser.add_argument(
            "--memcached",
            action="store_true",
            help="add memcached support [default: %(default)s]",
        )
        parser.add_argument(
            "--patch",
            action="store_true",
            help="apply LocalSettings.php patches [default: %(default)s]",
        )
        parser.add_argument(
            "-pu", "--plantuml", action="store_true", help="install plantuml"
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="start the update script -e.g. to fix SMW key",
        )
        parser.add_argument(
            "-wuc", "--wikiuser_check", action="store_true", help="check wikiuser"
        )
        return parser

    def handle_args(self, args) -> bool:
        handled = super().handle_args(args)
        if handled:
            return True
        if args.info:
            info = self.pw.system_info()
            print(info)
            return True
        return False

    def run(self, argv=None) -> int:
        args = self.parse_args(argv)
        handled = self.handle_args(args)
        if not handled:
            self.pw.work(args)
        return self.exit_code


def main(argv: List[str] = None) -> int:
    return ProfiWikiCmd.main(version=Version, argv=argv)


if __name__ == "__main__":
    sys.exit(main())

