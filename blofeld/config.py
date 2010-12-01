# Blofeld - All-in-one music server
# Copyright 2010 Dave Hayes <dwhayes@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import sys
import traceback

import platform
import ConfigParser

import anyjson

from blofeld.utils import get_main_dir

if platform.system() == 'Windows':
    from win32com.shell import shellcon, shell
if platform.system() == 'Linux':
    from xdg import BaseDirectory

__all__ = ['cfg']

class Config(dict):

    def __init__(self, installed=False, system=False, program_dir=None, 
                                                                    path=None):
        dict.__init__(self)
        self.path = path
        if not program_dir:
            program_dir = get_main_dir()
        if not installed:
            if platform.system() == 'Windows':
                installed_path = os.path.join(shell.SHGetFolderPath(0,
                                shellcon.CSIDL_PROGRAM_FILES, 0, 0), 'Blofeld')
                if os.path.normcase(os.path.abspath(program_dir)) == \
                   os.path.normcase(os.path.abspath(installed_path)):
                    installed = True
            else:
                installed = os.getenv('BLOFELD_INSTALLED')
        if not system:
            system = os.getenv('BLOFELD_SYSTEM_WIDE')
        self['PROGRAM_DIR'] = program_dir
        self['ASSETS_DIR'] = self['PROGRAM_DIR']
        if system:
            self['CONFIG_DIR'] = '/etc/blofeld'
            self['LOG_DIR'] = '/var/log/blofeld'
            self['CACHE_DIR'] = '/var/cache/blofeld'
        elif installed:
            if platform.system() == 'Windows':
                self['CONFIG_DIR'] = os.path.join(shell.SHGetFolderPath(0,
                                      shellcon.CSIDL_APPDATA, 0, 0), 'Blofeld')
            elif platform.system() == 'Linux':
                self['CONFIG_DIR'] = BaseDirectory.save_config_path('blofeld')
            else:
                self['CONFIG_DIR'] = os.path.join(os.path.expanduser("~"),
                                                  '.blofeld')
            self['LOG_DIR'] = os.path.join(self['CONFIG_DIR'], 'log')
            self['CACHE_DIR'] = os.path.join(self['CONFIG_DIR'], 'cache')
        else:
            self['CONFIG_DIR'] = self['PROGRAM_DIR']
            self['LOG_DIR'] = os.path.join(self['PROGRAM_DIR'], 'log')
            self['CACHE_DIR'] = os.path.join(self['PROGRAM_DIR'], 'cache')
        for item in os.listdir(self['CACHE_DIR']):
            if item.endswith('.zip'):
                try:
                    os.remove(os.path.join(self['CACHE_DIR'], item))
                except:
                    pass

    def save_config(self):
        self._cfg.set('server', 'host', str(self['HOSTNAME']))
        self._cfg.set('server', 'port', str(self['PORT']))
        self._cfg.set('security', 'require_login', anyjson.serialize(self['REQUIRE_LOGIN']))
        self._cfg.set('security', 'users', anyjson.serialize(self['USERS']))
        self._cfg.set('security', 'groups', anyjson.serialize(self['GROUPS']))
        self._cfg.set('database', 'path', str(os.path.abspath(self['MUSIC_PATH'])))
        self._cfg.set('database', 'couchdb_url', str(self['COUCHDB_URL']))
        self._cfg.set('database', 'couchdb_user', str(self['COUCHDB_USER']))
        self._cfg.set('database', 'couchdb_password', str(self['COUCHDB_PASSWORD']))
        self._cfg.set('interface', 'theme', str(self['THEME']))
        with open(self['CONFIG_FILE'], 'w') as conf_file:
            self._cfg.write(conf_file)

    def load_config(self):
        if not os.path.isdir(self['CONFIG_DIR']):
            os.mkdir(self['CONFIG_DIR'])
            
        if self.path:
            if not os.path.exists(self.path):
                raise Exception("Configuration file does not exist!")
            else:
                self['CONFIG_FILE'] = self.path
        else:
            self['CONFIG_FILE'] = os.path.join(self['CONFIG_DIR'],
                                               'blofeld.cfg')

        if not os.path.isdir(self['CACHE_DIR']):
            os.mkdir(self['CACHE_DIR'])
        self['PID_FILE'] = os.path.join(self['CACHE_DIR'], 'blofeld.pid')
        if not os.path.isdir(self['LOG_DIR']):
            os.mkdir(self['LOG_DIR'])

        self._cfg = ConfigParser.SafeConfigParser()

        # Load the configuration file, or create one with the defaults.
        if not os.path.exists(self['CONFIG_FILE']) and not self.path:
            self._cfg.add_section('server')
            self._cfg.set('server', 'host', '0.0.0.0')
            self._cfg.set('server', 'port', '8083')
            self._cfg.add_section('security')
            self._cfg.set('security', 'require_login', 'false')
            self._cfg.set('security', 'users', anyjson.serialize({
                'admin': 'password',
                'user': 'password'
                }))
            self._cfg.set('security', 'groups', anyjson.serialize({
                'admin': ['admin'],
                'download': ['admin', 'user']
            }))
            self._cfg.add_section('database')
            if platform.system == 'Windows':
                music_path = shell.SHGetFolderPath(0, shellcon.CSIDL_MYMUSIC,
                                                   0, 0)
            else:
                music_path = os.path.join(os.path.expanduser("~"), "Music")
            self._cfg.set('database', 'path', music_path)
            self._cfg.set('database', 'couchdb_url', 'http://localhost:5984')
            self._cfg.set('database', 'couchdb_user', '')
            self._cfg.set('database', 'couchdb_password', '')
            self._cfg.add_section('interface')
            self._cfg.set('interface', 'theme', 'default')
            with open(self['CONFIG_FILE'], 'w') as conf_file:
                self._cfg.write(conf_file)
            print "No configuration file was found, so we created one for you at %s. Please check it and make sure everything looks OK before running Blofeld again." % self['CONFIG_FILE']
            sys.exit()
        else:
            self._cfg.read(self['CONFIG_FILE'])


        self['MUSIC_PATH'] = unicode(self._cfg.get('database', 'path'))
        if not os.path.isdir(self['MUSIC_PATH']):
            raise Exception("Music path does not exist!")

        self['REQUIRE_LOGIN'] = self._cfg.getboolean('security', 
                                                     'require_login')
        self['USERS'] = anyjson.deserialize(self._cfg.get('security',
                                                          'users'))
        self['GROUPS'] = anyjson.deserialize(self._cfg.get('security', 
                                                           'groups'))
        self['COUCHDB_URL'] = self._cfg.get('database',
                                            'couchdb_url')
        self['COUCHDB_USER'] = self._cfg.get('database',
                                             'couchdb_user')
        self['COUCHDB_PASSWORD'] = self._cfg.get('database',
                                                 'couchdb_password')
        self['HOSTNAME'] = self._cfg.get('server',
                                         'host')
        self['PORT'] = self._cfg.getint('server',
                                        'port')
        self['THEME'] = self._cfg.get('interface', 'theme')
        self['THEME_DIR'] = os.path.join(self['ASSETS_DIR'], 'interfaces',
                                         self['THEME'],
                                         'templates')

        if sys.getfilesystemencoding() == 'ANSI_X3.4-1968':
            self['ENCODING'] = 'utf-8'
        else:
            self['ENCODING'] = sys.getfilesystemencoding()
        self['MUSIC_EXTENSIONS'] = [
            'mp3',     # MPEG-2 Layer III
            'ogg',     # Ogg Vorbis
            'oga',     # Ogg Vorbis
            'aac',     # Advanced Audio Coding
            'mp4',     # MPEG-4 (usually contains AAC)
            'm4a',     # MPEG-4 (usually contains AAC)
            'flac',    # FLAC
            'wma',     # Windows Media Audio
            'mp2'      # MPEG-2
            ]

        self['COVER_EXTENSIONS'] = [
            "jpg",
            "jpeg",
            "png",
            "gif",
            "tif",
            "tiff",
            "bmp"
        ]

        self['COVER_NAMES'] = [
            "folder",
            "cover",
            "front",
            "coverart"
        ]

        self['CHERRYPY_OUTPUT'] = False

cfg = Config()
cfg.load_config()

if os.path.exists(cfg['PID_FILE']) and traceback.extract_stack()[0][0] != 'Blofeld.py':
    try:
        import cPickle as pickle
    except:
        import pickle
    with open(cfg['PID_FILE']) as pidfile:
        state = pickle.load(pidfile)
    del cfg
    cfg = state['cfg']
    cfg.load_config()
    options = state['options']
    from blofeld.log import *
    if options.log_file:
        enable_single_file(options.log_file)
    else:
        enable_file()
    if options.daemonize:
        pass
    elif options.debug:
        enable_console('debug')
    elif options.verbose:
        enable_console('info')
    elif options.quiet:
        enable_console('critical')
    else:
        enable_console()
