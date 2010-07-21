#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_scripts import install_scripts
import sys
import os


#class InstallScripts(install_scripts):
#    def run(self):
#        os.symlink(os.path.join(prefix, 'share', 'blofeld', 'Blofeld.py'),
#        os.path.join(install_scripts, 'blofeld'))
#        install_scripts.run(self)

extra_files = [(os.path.join('share', 'blofeld'), ['Blofeld.py'])]

for path in ['views', 'interfaces']:
    for base, dirs, files in os.walk(path):
        if files:
            file_list = []
            for filename in files:
                file_list.append(os.path.join(base, filename))
            extra_files.append((os.path.join('share', 'blofeld', base), file_list))

setup(name = 'blofeld',
    version = '0.2',
    description = 'Web-based Music Server',
    author = 'Dave Hayes',
    author_email = 'dwhayes@gmail.com',
    url = 'http://github.com/daveisadork/Blofeld',
    license = 'GPL',
    long_description = \
"""This is a music server that does automatic on-the-fly transcoding, has a themeable web interface, cover art support and much more.""",
    platforms = ['POSIX'],
    packages = ['blofeld', 'blofeld.library', 'blofeld.utils'],
    data_files = extra_files,
    scripts = ['scripts/blofeld'],
#    cmdclass={'install_scripts': InstallScripts}
    )


