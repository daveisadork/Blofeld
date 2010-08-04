#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_scripts import install_scripts


import sys
import os


assets = [(os.path.join('share', 'blofeld'), ['Blofeld.py'])]

for path in ['views', 'interfaces']:
    for base, dirs, files in os.walk(path):
        if files:
            file_list = []
            for filename in files:
                file_list.append(os.path.join(base, filename))
            assets.append((os.path.join('share', 'blofeld', base), file_list))

setup(name = 'blofeld',
    version = '0.2.3',
    description = 'Web-based Music Server',
    author = 'Dave Hayes',
    author_email = 'dwhayes@gmail.com',
    url = 'http://github.com/daveisadork/Blofeld',
    license = 'GPL',
    long_description = \
"""This is a music server that does automatic on-the-fly transcoding, has a themeable web interface, cover art support and much more.""",
    platforms = ['POSIX'],
    packages = ['blofeld', 'blofeld.library', 'blofeld.utils'],
    data_files = assets,
    scripts = ['scripts/blofeld'],
    )


