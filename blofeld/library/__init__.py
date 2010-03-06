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


from time import time
import thread

from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader

from blofeld.config import *
import blofeld.util as util


class Library:
    """This is the Blofeld library module. It handles loading songs from the
    various backends (such as the filesystem or Rhythmbox) and inserting 
    their metadata into the database. It also handles making calls to the
    database.
    """
    def __init__(self):
        """Sets up the database connection and starts loading songs."""
        # Initiate a connection to the database server
        URL = 'http://localhost:5984'
        self._server = Server(URL)
        # Get a reference to our database
        self.db = self._server.get_or_create_db("blofeld")
        # Load our database views from the filesystem
        loader = FileSystemDocsLoader(os.path.join(PROGRAM_DIR,
                                      'views/_design'))
        loader.sync(self.db, verbose=True)
        # Spawn a new thread to start the backend
        thread.start_new_thread(self._load_songs, ())
#        self._load_songs()

    def _load_songs(self):
        """Figures out which backend to load and then updates the database"""
        start_time = time()
        if USE_RHYTHMBOX:
            print "Importing Rhythmbox database..."
            from blofeld.library.rhythmbox import load_rhythmbox_db
            load_rhythmbox_db(RB_DATABASE, self.db)
        if USE_FILESYSTEM:
            print "Starting filesystem scan..."
            from blofeld.library.filesystem import load_music_from_dir
            load_music_from_dir(MUSIC_PATH, self.db)
        print "Updated database in " + str(time() - start_time) + " seconds."
        # Compact the database so it doesn't get too huge. Really only needed
        # if we've added a bunch of files, maybe we should check for that.
        self.db.compact()

    def songs(self, artists=None, albums=None, query=None):
        '''Returns a list of songs as dictionary objects.'''
        # Create a list to hold the results
        result = []
        # If the client didn't supply any arguments, just get all the songs
        # from the database and append each one to our results list.
        if not query and not artists and not albums:
            for song in self.db.view('songs/all'):
                result.append(song['value'])
        if query:
            # Clean up the search string
            query = util.clean_text(query)
            # Get all the songs from the database.
            for song in self.db.view('songs/all'):
                # Create a searchable string by joining together the artist,
                # album and title fields and cleaning them up.
                search_field = util.clean_text(";".join([song['key'][0],
                                            song['key'][1], song['key'][3]]))
                # Find out if our search term is in there anywhere, and if so,
                # append the song to our results list.
                if query in search_field:
                    result.append(song['value'])
        if artists:
            # Check if we've already found some songs
            if result:
                # Create a list to hold the subset of songs we'll get by
                # refining our existing results.
                temp_result = []
                # Search through the current results for any songs by the
                # specified artist(s) and add them to our temporary list.
                for song in result:
                    if song['artist_hash'] in artists:
                        temp_result.append(song)
                # Replace the existing results with our refined ones
                result = temp_result
            # Since our results are empty, make sure that's not because the
            # search just didn't have any results, in which case we want to 
            # return an empty list.
            elif not query:
                # Get all the songs from the database and find the ones by
                # the specified artist, then append them to our results list.
                for song in self.db.view('songs/all'):
                    if song['value']['artist_hash'] in artists:
                        result.append(song['value'])
        if albums:
            # Check whether we already have a list of songs we need to refine.
            if result:
                # Create a list to hold the results of our refinement operation
                temp_result = []
                # Look through our existing results and add the ones that are
                # from the specified album(s) to our temporary list.
                for song in result:
                    if song['album_hash'] in albums:
                        temp_result.append(song)
                # Replace the existing results with our refined ones
                result = temp_result
            # Since our results are empty, make sure that's not because the
            # search just didn't have any results, in which case we want to 
            # return an empty list.
            elif not query:
                # Get all the songs from the database and find the ones from
                # the specified album(s), then append them to our results list.
                for song in self.db.view('songs/all'):
                    if song['value']['album_hash'] in albums:
                        result.append(song['value'])
        return result

    def albums(self, artists=None, query=None):
        '''Returns a list of albums as dictionary objects.'''
        print "Generating album list..."
        # Make a list to hold the results of our search
        result = []
        # If the client didn't give any arguments, get all the artists from the
        # database and append them to our results list.
        if not artists and not query:
            for album in self.db.view('albums/all', group="true"):
                result.append({'id': album['value'], 'title': album['key']})
        if query and artists:
            # Clean up the search term 
            query = util.clean_text(query)
            # Get all the albums from the database using the search view
            for album in self.db.view('albums/search'):
                # Create an object that we can append to the results list
                entry = {
                        'id': album['value']['album_hash'],
                        'title': album['key']
                        }
                # Clean up the search field and see if our search term is
                # in it.
                if query in util.clean_text(album['value']['search_string']):
                    # Make sure this album is not already in the results
                    # list so we don't end up with duplicates and make sure
                    # the album is by an artist the client specified. Then
                    # append it to the results list.
                    if entry not in result and \
                        album['value']['artist_hash'] in artists:
                        result.append(entry)
        if query and not artists:
            # Clean up the search term 
            query = util.clean_text(query)
            # Get all the albums from the database using the search view
            for album in self.db.view('albums/search'):
                # Create an object that we can append to the results list
                entry = {
                    'id': album['value']['album_hash'],
                    'title': album['key']
                    }
                # Clean up the search field and see if our search term is
                # in it. If it is, make sure it's not a duplicate result
                # and then append it to the results list.
                if query in util.clean_text(album['value']['search_string']):
                    if entry not in result:
                        result.append(entry)
        if artists and not query:
            # Get all the albums from the library
            for album in self.db.view('albums/by_artist'):
                # Create an object to append to our results list
                entry = {
                    'id': album['value']['album_hash'],
                    'title': album['key']
                    }
                # Get the artist ID
                artist = album['value']['artist']
                # Make sure the album is by an artist the client requested and
                # that it's not a duplicate result, then append it to the list.
                if artist in artists and entry not in result:
                    result.append(entry)
        return result

    def artists(self, query=None):
        '''Returns a list of artists as dictionary objects.'''
        print "Generating artist list..."
        # Make a list to hold the results of our search
        result = []
        if query:
            # Clean up the search term
            query = util.clean_text(query)
            # Get all the artists from the database using the search view,
            # the key of which is a list consisting of [artist, album, title].
            # This is done so that the results will be alphabetized by artist
            # name and also so we have those fields to search.
            for artist in self.db.view('artists/search'):
                # Create an object to append to our results
                entry = {
                    'id': artist['value'],
                    'name': artist['key'][0]
                    }
                # Create a search field consisting of artist;album;title
                search_field =  util.clean_text(';'.join(artist['key']))
                # Make sure our search term is in the search field and this
                # artist won't be a duplicate result and then add it to the
                # list.
                if query in search_field and entry not in result:
                    result.append(entry)
        else:
            # Get all the artists from the database and append them to the
            # results list.
            for artist in self.db.view('artists/all', group="true"):
                entry = {
                    'id': artist['value'],
                    'name': artist['key']
                    }
                result.append(entry)
        return result

