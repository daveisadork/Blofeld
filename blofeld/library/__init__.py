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

from uuid import uuid4
#import desktopcouch
from couchdb.client import *
#from desktopcouch import local_files

#from blofeld.library.util import OAuthCapableServer
from blofeld.config import *

URL = 'http://localhost:5984'
server = Server(URL)
if 'blofeld' not in server:
    db = server.create('blofeld')
else:
    db = server['blofeld']

if USE_RHYTHMBOX:
    from blofeld.library.rhythmbox import load_rhythmbox_db
    artists, albums, songs, relationships = load_rhythmbox_db(RB_DATABASE)
#    artists, albums, songs, relationships = load_rhythmbox_db("/home/dhayes/Desktop/rhythmdb.xml")
#    for artist in artists:
#        print artists[artist]
#        db[uuid4().hex] = {
#            'type': 'artist',
#            'value': artists[artist]
#        }

#    for album in albums:
#        print albums[album]
#        db[uuid4().hex] = {
#            'type': 'album',
#            'artist': 
#            'value': albums[album]
#        }

#    for song in songs:
#        print songs[song]['title']
#        songs[song]['type'] = 'song'
#        db[uuid4().hex] = songs[song]

#    database = {}
#    for artist in relationships:
#        database[artist] = {}
#        database[artist]['name'] = artists[artist]
#        database[artist]['albums'] = {}
#        for album in relationships[artist]:
#            database[artist]['albums'][album] = {}
#            database[artist]['albums'][album]['title'] = albums[album]
#            database[artist]['albums'][album]['songs'] = {}
#            for song in relationships[artist][album]:
#                database[artist]['albums'][album]['songs'][song] = songs[song]
#    for record in database:
#        db[record] = database[record]
