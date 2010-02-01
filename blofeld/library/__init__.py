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
import view

class Library:
    def __init__(self):
        URL = 'http://localhost:5984'
        self.server = Server(URL)
        if 'blofeld' not in self.server:
            self.create_db()
        else:
            self.db = self.server['blofeld']
        self.querying_db = False
        self.records = {}
        self.update()
        thread.start_new_thread(self.update_db, ())
#        self.update_db()

    def create_db(self):
        self.db = self.server.create('blofeld')
        self.db['_design/songs'] = view.songs

    def update_db(self):
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
#        print "Cleaning library..."
#        start_time = time()
#        for song in self.db.view("_all_docs"):
#            if song.id not in keys and "_" not in song.id:
#                del self.db[song.id]
#        print "Cleaned library in " + str(time() - start_time) + " seconds."
        self.db.compact()
        self.update()

    def songs(self):
        if time() - self.last_update > 10.0:
            thread.start_new_thread(self.update, ())
        return self.records


    def albums(self):
        print "Generating album list..."
        def list_albums():
            albumlist = []
            for record in self.records:
                if self.records[record]['album_hash'] not in albumlist:
                    albumlist.append(self.records[record]['album_hash'])
                    yield self.records[record]['album_hash'], self.records[record]['album']
        return dict(list_albums())

    def artists(self):
        print "Generating artist list..."
        def list_artists():
            artistlist = []
            for record in self.records:
                if self.records[record]['artist_hash'] not in artistlist:
                    artistlist.append(self.records[record]['artist_hash'])
                    yield self.records[record]['artist_hash'], self.records[record]['artist']
        return dict(list_artists())

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
        if self.querying_db == True:
            return
        self.last_update = time()
        self.querying_db = True
        print "Querying database..."
        for song in self.db.view('songs/all'):
            if song.id in self.records:
                self.records[song.id].update(song.value)
            else:
                self.records[song.id] = song.value
        self.querying_db = False
        print "Query complete."
        #thread.start_new_thread(self.clean, ())
        self.clean()

    def clean(self):
        if self.querying_db == True:
            return
        print "Cleaning songs..."
        start_time = time()
        remove = self.records.keys()
        current_db = []
        self.querying_db = True
        for song in self.db.view("_all_docs"):
            try:
                remove.remove(song.id)
            except:
                pass
        self.querying_db = False
#        for song in self.records:
#            if song not in current_db:
#                remove.append(song)
        for song in remove:
            del self.records[song]
        print "Cleaned", len(remove), "songs in", time() - start_time, "seconds."
