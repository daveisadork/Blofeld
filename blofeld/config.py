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

import ConfigParser

PROGRAM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                              os.pardir))
CONFIG_FILE = os.path.join(PROGRAM_DIR, 'blofeld.cfg')
LOG_DIR = os.path.join(PROGRAM_DIR, 'logs')
CACHE_DIR = os.path.join(PROGRAM_DIR, 'cache')

if not os.path.isdir(CACHE_DIR):
    os.mkdir(CACHE_DIR)

if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

from blofeld.log import logger

_cfg = ConfigParser.ConfigParser()

# Load the configuration file, or create one with the defaults.
if not os.path.exists(CONFIG_FILE):
    _cfg.add_section('server')
    _cfg.set('server', 'use_internal', 'True')
    _cfg.set('server', 'host', '0.0.0.0')
    _cfg.set('server', 'port', '8083')
    _cfg.add_section('database')
    _cfg.set('database', 'path',
             os.path.join(os.path.expanduser("~"), "Music"))
    _cfg.add_section('interface')
    _cfg.set('interface', 'theme', 'default')
    with open(CONFIG_FILE, 'w') as conf_file:
        _cfg.write(conf_file)
else:
    _cfg.read(CONFIG_FILE)

USE_INTERNAL = _cfg.getboolean('server', 'use_internal')

MUSIC_PATH = _cfg.get('database', 'path')
if not os.path.isdir(MUSIC_PATH):
    logger.critical("Music path does not exist!")
    raise Exception("Music path does not exist!")

HOSTNAME = _cfg.get('server', 'host')
PORT = _cfg.getint('server', 'port')
THEME_DIR = os.path.join(PROGRAM_DIR, 'interfaces',
                         _cfg.get('interface', 'theme'), 'templates')

ENCODING = sys.getfilesystemencoding()
ACCEPTED_EXTENSIONS = [
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
