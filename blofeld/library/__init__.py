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
import urlparse
import os
import threading

from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader
from restkit import BasicAuth
import anyjson

from blofeld.config import cfg
from blofeld.library.filesystem import Scanner
import blofeld.utils as utils
from blofeld.log import logger


class BlofeldCache(dict):
    def __init__(self, db):
        self.db = db
        self.version = self.db.info()['update_seq']

    def view(self, view_name, obj=None, wrapper=None, **params):
        key = anyjson.serialize({
            'view_name': view_name,
            'obj': obj,
            'wrapper': wrapper,
            'params': params
            })
        if not self.has_key(key):
            self[key] = {
                'version': 0,
                'view': self.db.view(view_name, obj, wrapper, **params)
                }
        self.version = self.db.info()['update_seq']
        if self[key]['version'] < self.version:
            self[key]['version'] = self.version
            self[key]['view'].fetch()
        else:
            logger.debug("Successful cache hit for %s" % key)
        return self[key]['view']


class Library:
    """This is the Blofeld library module. It handles loading songs from the
    various backends (such as the filesystem or Rhythmbox) and inserting
    their metadata into the database. It also handles making calls to the
    database.
    """
    def __init__(self, db_url=cfg['COUCHDB_URL'],
                  db_username=cfg['COUCHDB_USER'],
                  db_password=cfg['COUCHDB_PASSWORD']):
        """Sets up the database connection and starts loading songs."""
        # Initiate a connection to the database server
        self.shutting_down = threading.Event()
        self.building_cache = threading.Event()
        logger.debug("Initiating the database connection.")
        auth = BasicAuth(db_username, db_password)
        self._server = Server(db_url, filters=[auth])
        # Get a reference to our database
        self.db = self._server.get_or_create_db(cfg['DATABASE_NAME'])
        logger.debug("Loading database design documents.")
        # Load our database views from the filesystem
        loader = FileSystemDocsLoader(os.path.join(cfg['ASSETS_DIR'],
                                      'views/_design'))
        try:
            loader.sync(self.db, verbose=True)
        except:
            pass
        logger.debug("Initializing the database cache.")
        self.cache = BlofeldCache(self.db)
        self.scanner = Scanner(cfg['MUSIC_PATH'], self.db)
        self.update()

    def update(self, verbose=False, ticket=None):
        """Figures out which backend to load and then updates the database"""
        if ticket:
            status = self.scanner.jobs[self.scanner.current_job]
            if self.scanner.updating.is_set():
                total_time = time() - self.scanner.start_time
            else:
                total_time = status['total_time']
            minutes = total_time / 60
            hours = minutes / 60
            if hours:
                minutes = minutes % 60
            seconds = total_time % 60
            status['total_time'] = "%02d:%02d:%02d" % (hours, minutes, seconds)
            return status
        else:
            ticket = self.scanner.update()
            self.build_cache()
            self.scanner.updating.wait(None)
            return ticket

    def stop(self):
        logger.info("Preventing new library calls.")
        self.shutting_down.set()
        self.scanner.stop()

    def build_cache(self):
        if not self.building_cache.is_set():
            self.cache_thread = threading.Thread(target=self._build_cache)
            self.cache_thread.start()
        else:
            logger.debug("Database cache build requested, but already in progress.")

    def _build_cache(self):
        if self.scanner.updating.is_set():
            self.scanner.finished.wait(None)
            self.scanner.finished.clear()
        logger.debug("Building the database cache.")
        self.building_cache.set()
        start_time = time()
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            self.artists()
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            self.albums()
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            self.songs(suggest="The")
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            self.artists(query="The")
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            self.albums(query="The")
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            self.songs(query="The")
        self.building_cache.clear()
        if not (self.shutting_down.is_set() or self.scanner.updating.is_set()):
            logger.debug("Finished building the database cache in %0.2d seconds." % (time() - start_time))
        else:
            logger.debug("Database cache building was interrupted after %0.2d seconds." % (time.time() - start_time))

    def songs(self, artists=None, albums=None, query=None, suggest=None):
        '''Returns a list of songs as dictionary objects.'''
        logger.debug("Generating song list.")
        start_time = time()
        # Create a list to hold songs we're going to return to the client
        result = []
        if suggest:
            if query:
                query = utils.clean_text(query)
                for song in self.cache.view('search/suggestion', group="true"):
                    if utils.clean_text(song['key']).startswith(query):
                        result.append(song['key'])
                        if len(result) == 10:
                            break
            else:
                for song in self.cache.view('search/suggestion', group="true"):
                    result.append(song['key'])
            finish_time = time() - start_time
            logger.debug("Generated list of %d songs in %0.2f seconds." % (len(result), finish_time))
            return result
        # If the client didn't supply any arguments, we just get all the songs
        # from the database
        if not query and not artists and not albums:
            for song in self.cache.view('songs/all'):
                result.append(song['value'])
        if artists:
            # The client only wants songs by a specific artist(s)
            for artist in artists:
                for song in self.cache.view('songs/by_artist_id', key=artist):
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
                    for song in self.cache.view('songs/by_album_id', key=album):
                        result.append(song['value'])
        if query:
            # Clean up the search string
            query = utils.clean_text(query).split(' ')
            # Figure out whether we already have some songs we need to filter
            # or if we need to grab them all from the database.
            if not (albums or artists):
                # Get all the songs from the database.
                for song in self.cache.view('songs/all'):
                    # Create a searchable string by joining together the artist,
                    # album and title fields and cleaning them up.
                    search_field = utils.clean_text(";".join([song['key'][0],
                                              song['key'][1], song['key'][3]]))
                    match = True
                    for term in query:
                        if term not in search_field:
                            match = False
                    if match:
                        result.append(song['value'])
            elif result:
                temp_result = []
                # Look through our existing results for any songs that contain
                # our search term.
                for song in result:
                    search_field = utils.clean_text(";".join([song['artist'],
                                                song['album'], song['title']]))
                    match = True
                    for term in query:
                        if term not in search_field:
                            match = False
                    if match:
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
            for album in self.cache.view('albums/all', group="true"):
                result.append({'id': album['value'], 'title': album['key']})
        if query and artists:
            # Clean up the search term
            query = utils.clean_text(query).split(' ')
            for artist in artists:
                # Get all the albums from the database using the search view
                for album in self.cache.view('albums/search', key=artist):
                    # Create an object that we can append to the results list
                    entry = {
                            'id': album['value']['album_hash'],
                            'title': album['value']['album']
                            }
                    if entry in result:
                        continue
                    match = True
                    for term in query:
                        if term not in utils.clean_text(album['value']['search_string']):
                            match = False
                    if match:
                        result.append(entry)
        if query and not artists:
            # Clean up the search term
            query = utils.clean_text(query).split(' ')
            # Get all the albums from the database using the search view
            for album in self.cache.view('albums/search'):
                # Create an object that we can append to the results list
                entry = {
                    'id': album['value']['album_hash'],
                    'title': album['value']['album']
                    }
                if entry in result:
                    continue
                # Clean up the search field and see if our search term is
                # in it. If it is, make sure it's not a duplicate result
                # and then append it to the results list.
                match = True
                for term in query:
                    if term not in utils.clean_text(album['value']['search_string']):
                        match = False
                if match:
                    result.append(entry)
        if artists and not query:
            # Client asked for albums by a specific artist(s), so get only
            # those albums from the database.
            for artist_hash in artists:
                for album in self.cache.view('albums/by_artist_id',
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
            query = utils.clean_text(query).split(' ')
            # Get all the artists from the database using the search view,
            # the key of which is a list consisting of [artist, album, title].
            # This is done so that the results will be alphabetized by artist
            # name and also so we have those fields to search.
            for artist in self.cache.view('artists/search'):
                # Create an object to append to our results
                entry = {
                    'id': artist['value'],
                    'name': artist['key'][0]
                    }
                if entry in result:
                    continue
                search_field =  utils.clean_text(';'.join(artist['key']))
                match = True
                for term in query:
                    if term not in search_field:
                        match = False
                if match:
                    result.append(entry)
        else:
            # Get all the artists from the database and append them to the
            # results list.
            for artist in self.cache.view('artists/all', group="true"):
                entry = {
                    'id': artist['value'],
                    'name': artist['key']
                    }
                result.append(entry)
        finish_time = time() - start_time
        logger.debug("Generated list of %d artists in %0.2f seconds." % (len(result), finish_time))
        return result
