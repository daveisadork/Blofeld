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

#import desktopcouch
#from couchdb.client import *
#from desktopcouch import local_files

#from blofeld.library.util import OAuthCapableServer
from blofeld.config import *

#URL = 'http://' + local_files.get_bind_address() + ':' + desktopcouch.find_port()
#server = OAuthCapableServer(URL)
#if 'blofeld' not in server:
#    db = server.create('blofeld')
#else:
#    db = server['blofeld']

if USE_RHYTHMBOX:
    from blofeld.library.rhythmbox import load_rhythmbox_db
    artists, albums, songs, relationships = load_rhythmbox_db(RB_DATABASE)
#    counter = 0
#    for song in songs:
#        counter += 1
#        print counter
#        try:
#            db[song] = songs[song]
#        except:
#            pass
