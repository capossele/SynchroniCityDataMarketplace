# -*- coding: utf-8 -*-

import os
from recommonmark.parser import CommonMarkParser

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

extensions = []
templates_path = ['/home/docs/checkouts/readthedocs.org/readthedocs/templates/sphinx', 'templates', '_templates', '.templates']
source_suffix = ['.rst', '.md']		
source_parsers = {		
            '.md': CommonMarkParser,		
        }
master_doc = 'index'
project = u'SynchroniCity IoT Data Marketplace'
copyright = u'2018'
version = 'latest'
release = 'latest'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
htmlhelp_basename = 'SynchroniCity-IoT-Data-Marketplace'
html_theme = 'sphinx_rtd_theme'
file_insertion_enabled = False
latex_documents = [
  ('index', 'SynchroniCity-IoT-Data-Marketplace.tex', u'SynchroniCity IoT Data Marketplace',
   u'', 'manual'),
]

# Only import and set the theme if we're building docs locally
if not on_rtd:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    #html_style = 'https://www.fiware.org/style/fiware_readthedocs.css'
else:
    html_context = { 
        'css_files': [
            'https://media.readthedocs.org/css/sphinx_rtd_theme.css',
            'https://media.readthedocs.org/css/readthedocs-doc-embed.css'
        ]
    }

#'https://www.fiware.org/style/fiware_readthedocs.css',