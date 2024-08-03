"""
Created on 2023-04-09

@author: wf
"""

import re


class Patch:
    """
    A class for patch a text file
    """

    def __init__(self, file_path: str):
        """
        Initializes a Patch instance with the file path file to be patched.

        Args:
            file_path (str): The file path of the PHP file to be patched.
        """
        self.lines = []
        self.file_path = file_path
        # https://stackoverflow.com/a/3277516/1497139
        with open(self.file_path, "r", encoding="UTF-8") as file:
            while line := file.readline():
                self.lines.append(line.rstrip())

    def save(self):
        """
        save my lines
        """
        with open(self.file_path, "w") as f:
            for line in self.lines:
                f.write(f"{line}\n")

    def patch_mediawiki_config_var(self, var_name: str, var_value: str) -> None:
        """
        Patches a MediaWiki configuration variable in the PHP file with the given name and value.

        Args:
            var_name (str): The name of the configuration variable to be patched.
            var_value (str): The new value to be set for the configuration variable.

        Returns:
            None
        """
        # Define the regex pattern to match the configuration variable
        pattern = r"\$wg" + re.escape(var_name) + r"\s*=\s*[^\n]+"

        # Define the replacement string with the updated value
        replacement = f"$wg{var_name} = {var_value};"

        # Use fileinput to replace the matched line in the file
        for i, line in enumerate(self.lines):
            new_line = re.sub(pattern, replacement, line)
            self.lines[i] = new_line

    def add_text(self, text: str, avoid_duplication: bool = True):
        """
        Adds text avoiding duplication if specified

        Args:
            text (str): the text to add
            avoid_duplication(bool): if True avoid duplication of existing lines
        """
        new_lines = text.split("\n")
        for new_line in new_lines:
            do_add = True
            if avoid_duplication:
                do_add = not new_line in self.lines
            if do_add:
                self.lines.append(new_line)
