"""
Created on 2023-04-09

@author: wf
"""

import tempfile

from profiwiki.patch import Patch
from basemkit.basetest import Basetest


class TestPatch(Basetest):
    """
    test Patching
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def getTestfile(self):
        tmp = tempfile.NamedTemporaryFile(prefix="test", suffix=".php")
        return tmp.name

    def getPatch(self):
        # Create a temporary directory and a test PHP file with example variables
        test_file_path = self.getTestfile()
        with open(test_file_path, "w") as f:
            f.write("<?php\n\n")
            f.write("$wgSitename = 'MyWiki';\n")
            f.write("$wgLanguageCode = 'en';\n")
            f.write("$wgEnableEmail = true;\n")

        patch = Patch(test_file_path)
        return patch

    def checkPatch(self, patch, expected_content):
        """
        check the patch against the expected content
        """
        with open(patch.file_path) as f:
            contents = f.read()
            self.assertIn(expected_content, contents)

    def test_add(self):
        """
        test adding  lines
        """
        lines = """$wgRawHtml = true;
$wgAllowImageTag=true;"""
        patch = self.getPatch()
        self.assertEqual(5, len(patch.lines))
        patch.add_text(lines)
        self.assertEqual(7, len(patch.lines))
        patch.add_text(lines)
        self.assertEqual(7, len(patch.lines))

    def test_quirk(self):
        lines = """
        // modified by profiwiki
// allow raw HTML
$wgRawHtml = true;
// allow images
$wgAllowImageTag=true;
// InstantCommons allows wiki to use images from https://commons.wikimedia.org
$wgUseInstantCommons = true;
// avoid showing (expected) deprecation warnings
error_reporting(E_ERROR | E_WARNING | E_PARSE | E_NOTICE);
// https://www.mediawiki.org/wiki/Extension:UserFunctions
$wgUFEnabledPersonalDataFunctions = [
    'ip',
    'nickname',
    'realname',
    'useremail',
    'username',
];
// work around last line not copied
        """
        patch = self.getPatch()
        patch.add_text(lines)
        patch.file_path = self.getTestfile()
        patch.save()
        patch2 = Patch(patch.file_path)
        print(patch2.lines)

    def test_save(self):
        """
        test saving after having added a line
        """
        patch = self.getPatch()
        self.assertEqual(5, len(patch.lines))
        patch.add_text("// an extra line")
        patch.save()
        patch2 = Patch(patch.file_path)
        self.assertEqual(6, len(patch2.lines))

    def test_patch_mediawiki_config_var(self):
        """
        test patching a mediawiki configuration
        """
        # Test patching a configuration variable that exists in the file
        patch = self.getPatch()
        patch.patch_mediawiki_config_var("Sitename", "'NewWikiName'")
        patch.save()
        self.checkPatch(patch, "$wgSitename = 'NewWikiName';")
