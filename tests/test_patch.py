'''
Created on 2023-04-09

@author: wf
'''
from tests.basetest import Basetest
from profiwiki.patch import Patch
import os
import shutil
import tempfile

class TestPatch(Basetest):
    """
    test Patching
    """
    
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        
    def getPatch(self):
        # Create a temporary directory and a test PHP file with example variables
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test.php")
        with open(self.test_file_path, "w") as f:
            f.write("<?php\n\n")
            f.write("$wgSitename = 'MyWiki';\n")
            f.write("$wgLanguageCode = 'en';\n")
            f.write("$wgEnableEmail = true;\n")

        patch = Patch(self.test_file_path)
        return patch
    
    def checkPatch(self,patch,expected_content):
        with open(patch.file_path) as f:
            contents = f.read()
            self.assertIn(expected_content, contents)

    def tearDown(self):
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
        
    def test_add(self):
        """
        test adding  lines
        """
        lines="""$wgRawHtml = true;
$wgAllowImageTag=true;"""
        patch=self.getPatch()
        self.assertEqual(5,len(patch.lines))
        patch.add_text(lines)
        self.assertEqual(7,len(patch.lines))
        patch.add_text(lines)
        self.assertEqual(7,len(patch.lines))
        
    def test_save(self):
        """
        test saving after having added a line
        """
        patch=self.getPatch()
        self.assertEqual(5,len(patch.lines))
        patch.add_text("// an extra line")
        patch.save() 
        patch2=Patch(patch.file_path)
        self.assertEqual(6,len(patch2.lines))
         

    def test_patch_mediawiki_config_var(self):
        # Test patching a configuration variable that exists in the file
        patch=self.getPatch()
        patch.patch_mediawiki_config_var("Sitename", "'NewWikiName'")
        patch.save()
        self.checkPatch(patch,"$wgSitename = 'NewWikiName';")