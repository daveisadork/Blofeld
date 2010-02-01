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
from couchdb.client import *
import thread

from blofeld.config import *
import blofeld.util as util
import view

class Library:
    def __init__(self):
        URL = 'http://localhost:5984'
        self._server = Server(URL)
        self._instantiate_db()
        self.records = {}
        self.update()
        thread.start_new_thread(self._load_songs, ())
#        self.update_db()

    def _instantiate_db(self):
        if 'blofeld' not in self._server:
            self.db = self.server.create('blofeld')
        else:
            self.db = self._server['blofeld']
            self.db1 = self._server['blofeld']
            self.db2 = self._server['blofeld']
        views = [Document(view.songs),
            Document(view.artists),
            Document(view.albums)]
        self.db.update(views)

    def _load_songs(self):
        start_time = time()
        if USE_RHYTHMBOX:
            print "Importing Rhythmbox database..."
            from blofeld.library.rhythmbox import load_rhythmbox_db
            songs = load_rhythmbox_db(RB_DATABASE)
#            songs = load_rhythmbox_db("/home/dhayes/Desktop/rhythmdb.xml")
            insert = []
            for song in songs:
                document = Document(songs[song])
                document['_id'] = song
                insert.append(document)
            self.db.update(songs.values())
            keys = songs.keys()
        if USE_FILESYSTEM:
            print "Starting filesystem scan..."
            from blofeld.library.filesystem import load_music_from_dir
            load_music_from_dir(MUSIC_PATH, self.db, self.records)
        print "Updated database in " + str(time() - start_time) + " seconds."
        self.db.compact()
        self._clean()

    def songs(self, artists=None, albums=None, query=None, songid=None):
        if songid:
            return self.db.query('''
                function(doc) {
                    if (doc._id == ''' + songid + ''') {
                        emit(null, doc);
                    }''')[0].value
        result = {}
        if not query and not artists and not albums:
            for song in self.db.view('songs/all'):
                result[song.id] = song.value
        if query:
            query = util.clean_text(query)
            for song in self.db.view('songs/all'):
                for field in ['artist', 'album', 'title']:
                    if query in util.clean_text(song.value[field]):
                        result[song.id] = song.value
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
                    if song.value['artist_hash'] in artists:
                        result[song.id] = song.value
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
                    if song.value['album_hash'] in albums:
                        result[song.id] = song.value
        return result

    def albums(self, artists=None, query=None):
        print "Generating album list..."
        result = {}
        if not artists and not query:
            for album in self.db2.view('albums/all'):
                result[album.key] = album.value
        if query:
            query = util.clean_text(query)
            if artists:
                for album in self.db2.view('albums/search'):
                    if query in util.clean_text(album.value['search_string']):
                        result[album.key] = album.value
            else:
                for album in self.db2.view('albums/search'):
                    if query in util.clean_text(album.value['search_string']):
                        result[album.key] = album.value['title']
        if artists:
            artists = artists.split(',')
            if result:
                temp_result = {}
                for album in result:
                    if result[album]['artist_hash'] in artists:
                       temp_result[album] = result[album]['title']
                result = temp_result
            else:
                for album in self.db2.view('albums/by_artist'):
                    if album.value['artist'] in artists:
                        result[album.key] = album.value['title']
        return result

    def artists(self, query=None):
        print "Generating artist list..."
        result = {}
        if query:
            query = util.clean_text(query)
            for artist in self.db1.view('artists/search'):
                if query in util.clean_text(';'.join(artist.value)):
                    result[artist.key] = artist.value[0]
        else:
            for artist in self.db1.view('artists/all'):
                result[artist.key] = artist.value
        return result

    def relationships(self):
        print "Calculating relationships..."
        relalist = {}
        songs = self.songs()
        for record in songs:
            artist_hash = self.records[record]['artist_hash']
            album_hash= self.records[record]['album_hash']
            if artist_hash not in relalist:
                relalist[artist_hash] = {}
            if album_hash not in relalist[artist_hash]:
                relalist[artist_hash][album_hash] = []
            relalist[artist_hash][album_hash].append(record)
        return relalist

    def update(self):
        self.last_update = time()
        print "Querying database..."
        for song in self.db.view('songs/all'):
            if song.id in self.records:
                self.records[song.id].update(song.value)
            else:
                self.records[song.id] = song.value
        print "Query complete."

    def _clean(self):
        print "Cleaning songs..."
        start_time = time()
        remove = self.records.keys()
        current_db = []
        for song in self.db.view("_all_docs"):
            try:
                remove.remove(song.id)
            except:
                pass
        for song in remove:
            del self.records[song]
        print "Cleaned", len(remove), "songs in", time() - start_time, "seconds."
