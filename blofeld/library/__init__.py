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


from operator import itemgetter, attrgetter
from time import time
import threading


from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader

from blofeld.config import *
from blofeld.library.filesystem import load_music_from_dir
import blofeld.util as util
from blofeld.log import logger


class Library:
    """This is the Blofeld library module. It handles loading songs from the
    various backends (such as the filesystem or Rhythmbox) and inserting 
    their metadata into the database. It also handles making calls to the
    database.
    """
    def __init__(self, URL='http://localhost:5984'):
        """Sets up the database connection and starts loading songs."""
        # Initiate a connection to the database server
        self._server = Server(URL)
        # Get a reference to our database
        self.db = self._server.get_or_create_db("blofeld")
        # Load our database views from the filesystem
        loader = FileSystemDocsLoader(os.path.join(PROGRAM_DIR,
                                      'views/_design'))
        try:
            loader.sync(self.db, verbose=True)
        except:
            pass
        self.updating = threading.Lock()

    def update(self, verbose=False):
        """Figures out which backend to load and then updates the database"""
        if not self.updating.acquire(False):
            logger.warn("Library update requested, but one is already in progress.")
            return
        logger.info("Starting library update.")
        start_time = time()
        load_music_from_dir(MUSIC_PATH, self.db)
        finish_time = time() - start_time
        logger.info("Updated library in %0.2f seconds." % finish_time)
        self.updating.release()

    def songs(self, artists=None, albums=None, query=None):
        '''Returns a list of songs as dictionary objects.'''
        logger.debug("Generating song list.")
        start_time = time()
        # Create a list to hold songs we're going to return to the client
        result = []
        # If the client didn't supply any arguments, we just get all the songs
        # from the database
        if not query and not artists and not albums:
            for song in self.db.view('songs/all'):
                result.append(song['value'])
        if artists:
            # The client only wants songs by a specific artist(s)
            for artist in artists:
                for song in self.db.view('songs/by_artist_id', key=artist):
                    result.append(song['value'])
        if albums:
            # The client only wants songs from a specific album(s). We need
            # to see if we've already got some songs we just need to filter or
            # whether we need to grab some from the database.
            if result:
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
            elif not artists:
                # Grab the songs from the specified album(s) from the database
                for album in albums:
                    for song in self.db.view('songs/by_album_id', key=album):
                        result.append(song['value'])
        if query:
            # Clean up the search string
            query = util.clean_text(query)
            # Figure out whether we already have some songs we need to filter
            # or if we need to grab them all from the database.
            if not (albums or artists):
                # Get all the songs from the database.
                for song in self.db.view('songs/all'):
                    # Create a searchable string by joining together the artist,
                    # album and title fields and cleaning them up.
                    search_field = util.clean_text(";".join([song['key'][0],
                                              song['key'][1], song['key'][3]]))
                    if query in search_field:
                        result.append(song['value'])
            elif result:
                temp_result = []
                # Look through our existing results for any songs that contain
                # our search term.
                for song in result:
                    search_field = util.clean_text(";".join([song['artist'],
                                                song['album'], song['title']]))
                    if query in search_field:
                        temp_result.append(song)
                # Replace the existing results with the filtered ones.
                result = temp_result
        finish_time = time() - start_time
        logger.debug("Generated list of %d songs in %0.2f seconds." % (len(result), finish_time))
        return sorted(result, key=itemgetter('artist', 'album',
                                               'tracknumber'))

    def albums(self, artists=None, query=None):
        '''Returns a list of albums as dictionary objects.'''
        logger.debug("Generating album list.")
        start_time = time()
        # Create a list to hold the albums we're going to return to the client
        result = []
        # If the client didn't give any arguments, get all the artists from the
        # database and append them to our results list.
        if not artists and not query:
            for album in self.db.view('albums/all', group="true"):
                result.append({'id': album['value'], 'title': album['key']})
        if query and artists:
            # Clean up the search term 
            query = util.clean_text(query)
            for artist in artists:
                # Get all the albums from the database using the search view
                for album in self.db.view('albums/search', key=artist):
                    # Create an object that we can append to the results list
                    entry = {
                            'id': album['value']['album_hash'],
                            'title': album['value']['album']
                            }
                    # Clean up the search field and see if our search term is
                    # in it.
                    if query in util.clean_text(album['value']['search_string']):
                        # Make sure this album is not already in the results
                        # list so we don't end up with duplicates and make sure
                        # the album is by an artist the client specified. Then
                        # append it to the results list.
                        if entry not in result:
                            result.append(entry)
        if query and not artists:
            # Clean up the search term 
            query = util.clean_text(query)
            # Get all the albums from the database using the search view
            for album in self.db.view('albums/search'):
                # Create an object that we can append to the results list
                entry = {
                    'id': album['value']['album_hash'],
                    'title': album['value']['album']
                    }
                # Clean up the search field and see if our search term is
                # in it. If it is, make sure it's not a duplicate result
                # and then append it to the results list.
                if query in util.clean_text(album['value']['search_string']):
                    if entry not in result:
                        result.append(entry)
        if artists and not query:
            # Client asked for albums by a specific artist(s), so get only
            # those albums from the database.
            for artist_hash in artists:
                for album in self.db.view('albums/by_artist_id',
                                            key=artist_hash):
                    # Create an object to append to our results list
                    entry = {
                        'id': album['value']['album_hash'],
                        'title': album['value']['album']
                        }
                    # Get the artist ID
                    artist = album['key']
                    # Make sure this isn't a duplicate result
                    if entry not in result:
                        result.append(entry)
        finish_time = time() - start_time
        logger.debug("Generated list of %d albums in %0.2f seconds." % (len(result), finish_time))
        return sorted(result, key=itemgetter('title'))

    def artists(self, query=None):
        '''Returns a list of artists as dictionary objects.'''
        logger.debug("Generating artist list.")
        start_time = time()
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
        finish_time = time() - start_time
        logger.debug("Generated list of %d artists in %0.2f seconds." % (len(result), finish_time))
        return result

