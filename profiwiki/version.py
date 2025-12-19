"""
Created on 2023-04-01

@author: wf
"""

import profiwiki


class Version(object):
    """
    Version handling for ProfiWiki
    """

    name = "pyProfiWiki"
    description = """BITPlan's professional Semantic Mediawiki"""
    version = profiwiki.__version__
    date = "2023-04-01"
    updated = "2025-12-19"
    authors = "Wolfgang Fahl"
    doc_url = "https://wiki.bitplan.com/index.php/ProfiWiki"
    chat_url = "https://github.com/BITPlan/ProfiWiki/discussions"
    cm_url = "https://github.com/BITPlan/ProfiWiki"
    license = f"""Copyright 2015-2025 contributors. All rights reserved.
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""
    longDescription = f"""{name} version {version}
{description}
  Created by {authors} on {date} last updated {updated}"""
