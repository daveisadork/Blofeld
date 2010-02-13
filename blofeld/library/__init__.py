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


"""This is the Blofeld library module. It handles loading songs from the
various backends (such as Rhythmbox or the filesystem), storing their 
metadata in the database and making it available through a number of 
methods.
"""


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
        thread.start_new_thread(self._load_songs, ())
#        self._load_songs()

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

    def songs(self, artists=None, albums=None, query=None):
        '''Returns a list of songs as dictionary objects.'''
        result = []
        if not query and not artists and not albums:
            for song in self.db.view('songs/all'):
                result.append(song['value'])
        if query:
            query = util.clean_text(query)
            for song in self.db.view('songs/all'):
                if query in util.clean_text(";".join([song['key'][0],
                                            song['key'][1], song['key'][3]])):
                    result.append(song['value'])
        if artists:
            if result:
                temp_result = []
                for song in result:
                    if song['artist_hash'] in artists:
                        temp_result.append(song)
                result = temp_result
            else:
                for song in self.db.view('songs/all'):
                    if song['value']['artist_hash'] in artists:
                        result.append(song['value'])
        if albums:
            if result:
                temp_result = []
                for song in result:
                    if song['album_hash'] in albums:
                        temp_result.append(song)
                result = temp_result
            else:
                for song in self.db.view('songs/all'):
                    if song['value']['album_hash'] in albums:
                        result.append(song['value'])
        return result

    def albums(self, artists=None, query=None):
        '''Returns a list of albums as dictionary objects.'''
        print "Generating album list..."
        result = []
        if not artists and not query:
            for album in self.db.view('albums/all', group="true"):
                result.append({'id': album['value'], 'title': album['key']})
        if query:
            query = util.clean_text(query)
            if artists:
                for album in self.db.view('albums/search'):
                    entry = {'id': album['value']['album_hash'],
                             'artist': album['value']['artist_hash'],
                             'title': album['key']}
                    if query in util.clean_text(album['value']['search_string']):
                        if entry not in result:
                            result.append(entry)
            else:
                for album in self.db.view('albums/search'):
                    entry = {'id': album['value']['album_hash'], 'title': album['key']}
                    if query in util.clean_text(album['value']['search_string']):
                        if entry not in result:
                            result.append(entry)
        if artists:
            if result:
                temp_result = []
                for album in result:
                    if album['artist'] in artists:
                       temp_result.append(album)
                result = temp_result
            else:
                for album in self.db.view('albums/by_artist'):
                    entry = {'id': album['value']['album_hash'],
                                         'title': album['key']}
                    if album['value']['artist'] in artists:
                        if entry not in result:
                            result.append(entry)
        return result

    def artists(self, query=None):
        '''Returns a list of artists as dictionary objects.'''
        print "Generating artist list..."
        result = []
        if query:
            query = util.clean_text(query)
            for artist in self.db.view('artists/search'):
                entry = {'id': artist['value'], 'name': artist['key'][0]}
                if query in util.clean_text(';'.join(artist['key'])):
                    if entry not in result:
                        result.append(entry)
        else:
            for artist in self.db.view('artists/all', group="true"):
                result.append({'id': artist['value'], 'name': artist['key']})
        return result

