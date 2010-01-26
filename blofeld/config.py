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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os

import ConfigParser

PROGRAM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

_ini = ConfigParser.ConfigParser()
_ini.read(os.path.join(PROGRAM_DIR, 'config.ini'))

USE_RHYTHMBOX = _ini.getboolean('database', 'rhythmbox')
if USE_RHYTHMBOX:
    RB_DATABASE = os.path.join(os.path.expanduser("~"), ".local/share/rhythmbox/rhythmdb.xml")

HOSTNAME = _ini.get('server', 'host')
PORT = _ini.getint('server', 'port')
THEME_DIR = os.path.join(PROGRAM_DIR, 'interfaces', _ini.get('interface', 'theme'), 'templates')
