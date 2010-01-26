#!/usr/bin/env python
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

import cherrypy

from blofeld import Blofeld
from blofeld.config import *

if __name__ == "__main__":
    cherrypy.config.update({
        'server.socket_host': HOSTNAME,
        'server.socket_port': PORT,
        'tools.encode.on': True, 
        'tools.encode.encoding': 'utf-8'
        })

    static = {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(THEME_DIR, 'static')
        }

    conf = {
        '/static': static,
        '/blofeld/static': static
        }

    cherrypy.quickstart(Blofeld(), '/', config=conf)

