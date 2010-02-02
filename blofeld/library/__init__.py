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

from time import time
import thread

from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader

from blofeld.config import *
import blofeld.util as util


class Library:
    def __init__(self):
        URL = 'http://localhost:5984'
        self._server = Server(URL)
        self._instantiate_db()
#        thread.start_new_thread(self._load_songs, ())
        self._load_songs()

    def _instantiate_db(self):
        self.db = self._server.get_or_create_db("blofeld")
        loader = FileSystemDocsLoader(os.path.join(PROGRAM_DIR, 'views/_design'))
        loader.sync(self.db, verbose=True)

    def _load_songs(self):
        start_time = time()
        if USE_RHYTHMBOX:
            print "Importing Rhythmbox database..."
            from blofeld.library.rhythmbox import load_rhythmbox_db
            #load_rhythmbox_db(RB_DATABASE, self.db)
            load_rhythmbox_db("/home/dhayes/Desktop/rhythmdb.xml", self.db)
        if USE_FILESYSTEM:
            print "Starting filesystem scan..."
            from blofeld.library.filesystem import load_music_from_dir
            load_music_from_dir(MUSIC_PATH, self.db)
        print "Updated database in " + str(time() - start_time) + " seconds."
        self.db.compact()

    def songs(self, artists=None, albums=None, query=None, songid=None):
        result = {}
        if not query and not artists and not albums:
            for song in self.db.view('songs/all'):
                result[song['id']] = song['value']
        if query:
            query = util.clean_text(query)
            for song in self.db.view('songs/all'):
                for field in ['artist', 'album', 'title']:
                    if query in util.clean_text(song['value'][field]):
                        result[song['id']] = song['value']
        if artists:
            artists = artists.split(',')
            if result:
                temp_result = {}
                for song in result:
                    if result[song]['artist_hash'] in artists:
                        temp_result[song] = result[song]
                result = temp_result
            else:
                for song in self.db.view('songs/all'):
                    if song['value']['artist_hash'] in artists:
                        result[song['id']] = song['value']
        if albums:
            albums = albums.split(',')
            if result:
                temp_result = {}
                for song in result:
                    if result[song]['album_hash'] in albums:
                        temp_result[song] = result[song]
                result = temp_result
            else:
                for song in self.db.view('songs/all'):
                    if song['value']['album_hash'] in albums:
                        result[song['id']] = song['value']
        return result

    def albums(self, artists=None, query=None):
        print "Generating album list..."
        result = {}
        if not artists and not query:
            for album in self.db.view('albums/all'):
                result[album['key']] = album['value']
        if query:
            query = util.clean_text(query)
            if artists:
                for album in self.db.view('albums/search'):
                    if query in util.clean_text(album['value']['search_string']):
                        result[album['key']] = album['value']
            else:
                for album in self.db.view('albums/search'):
                    if query in util.clean_text(album['value']['search_string']):
                        result[album['key']] = album['value']['title']
        if artists:
            artists = artists.split(',')
            if result:
                temp_result = {}
                for album in result:
                    if result[album]['artist_hash'] in artists:
                       temp_result[album] = result[album]['title']
                result = temp_result
            else:
                for album in self.db.view('albums/by_artist'):
                    if album['value']['artist'] in artists:
                        result[album['key']] = album['value']['title']
        return result

    def artists(self, query=None):
        print "Generating artist list..."
        result = {}
        if query:
            query = util.clean_text(query)
            for artist in self.db.view('artists/search'):
                if query in util.clean_text(';'.join(artist['value'])):
                    result[artist['key']] = artist['value'][0]
        else:
            for artist in self.db.view('artists/all'):
                result[artist['key']] = artist['value']
        return result

