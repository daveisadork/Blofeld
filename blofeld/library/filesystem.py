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

from __future__ import division
import os
import hashlib
from time import time, sleep
import urllib
from multiprocessing import Pool
from Queue import Queue
import threading

import mutagen

from blofeld.config import cfg
from blofeld.log import logger


class Scanner:
    def __init__(self, music_path, couchdb):
        self.music_path = music_path
        self.couchdb = couchdb
        # Create queues for songs that need to be read and saved to the DB
        self.read_queue = Queue()
        self.db_queue = Queue()
        self.db_needs_updated = threading.Event()
        self.scanning = threading.Event()
        self.updating = threading.Event()
        self.cleaning = threading.Event()
        self.reading = threading.Event()
        self.db_working = threading.Event()


    def update(self):
        if self.updating.is_set():
            logger.warn("Library update requested, but one is already in progress.")
            return
        self.updating.set()
        # Clean the database of files that no longer exist and get a list of the
        # remaining songs in the database.
        self.records = self.clean()
        self.start_time = time()
        self.scan()
        # Spawn a new thread to handle the queue of files that need read.
        read_thread = threading.Thread(target=self.process_read_queue)
        read_thread.start()
        sleep(2)
        # Spawn a new thread to handle the queue of items that need added to the
        # database.
        db_thread = threading.Thread(target=self.add_items_to_db)
        db_thread.start()
        # Block while we wait for everything to finish
        self.db_working.wait(None)
        # Join our threads back
        read_thread.join()
        finish_time = time() - self.start_time
        logger.debug("Added all new songs in %0.2f seconds." % finish_time)
        compact_thread = threading.Thread(target=self.couchdb.compact)
        compact_thread.start()
        self.updating.clear()

    def status(self):
        if not self.updating.is_set():
            return {'status': 'Idle'}
        elif self.scanning.is_set():
            return {'status': 'Scanning'}
        elif self.reading.is_set():
            return {
                'status': 'Reading',
                'total_songs': self.songs_total,
                'remaining_songs': self.read_queue.qsize()
            }
        else:
            return None

    def scan(self):
        """Scans music_path for songs, adds new/changed songs to couchdb and
        removes any songs that have gone missing.
        """
        logger.debug("Scanning for new files.")
        self.scanning.set()
        changed = 0
        unchanged = 0
        # Iterate through all the folders and files in music_path
        for root, dirs, files in os.walk(self.music_path):
            for item in files:
                # Get the file extension, e.g. 'mp3' or 'flac', and see if it's in
                # the list of extensions we're supposed to look for.
                extension = os.path.splitext(item)[1].lower()[1:]
                if extension in cfg['MUSIC_EXTENSIONS']:
                    # Get the full decoded path of the file. The decoding part is
                    # important if the filename includes non-ASCII characters.
                    location = os.path.join(root, item)
                    # Generate a unique ID for this song by making a SHA-1 hash of
                    # its location.
                    id = hashlib.sha1(location.encode('utf-8')).hexdigest()
                    # Get the time that this file was last modified
                    mtime = str(os.stat(os.path.join(root, item))[8])
                    # Find out if this song is already in the database and if so
                    # whether it has been modified since the last time we scanned
                    # it.
                    try:
                        record_mtime = self.records[id]['mtime']
                    except:
                        record_mtime = None
                    if mtime != record_mtime:
                        try:
                            revision = self.records[id]['_rev']
                        except:
                            revision = None
                        # Add the song to the queue to be read
                        self.read_queue.put((location, id, mtime, extension, revision))
                    else:
                        unchanged += 1
        self.scanning.clear()
        if self.read_queue.qsize() < 1:
            logger.debug("No new files found.")
            return False
        self.songs_total = self.read_queue.qsize()
        logger.debug("Queued %d songs for reading." % self.read_queue.qsize())
        return True

    def add_items_to_db(self):
        # While the read queue is still being processed or we have stuff waiting
        # to be added to the database...
        self.db_working.set()
        while self.reading.is_set() or self.db_queue.qsize() > 0:
            if self.db_needs_updated.is_set() or self.db_needs_updated.wait(2.0):
                self.db_needs_updated.clear()
                songs = []
                while self.db_queue.qsize() > 0:
                    # Grab all the items out of the database queue
                    songs.extend(self.db_queue.get())
                updated = 0
                new = []
                for song in songs:
                    if song is None:
                        # There must've been a problem reading this file so 
                        # we'll skip it.
                        continue
                    else:
                        # Get the metadata ready to send to the database
                        new.append(song)
                        if "_rev" in song:
                            updated += 1
                # Make our changes to the database
                self.couchdb.bulk_save(new)
                logger.debug("Added %d songs to the database, %d of which already existed." % (len(new), updated))
        self.db_working.clear()

    def process_read_queue(self):
        # This lets the other processes know that we're working on reading files
        self.reading.set()
        # Create a pool of processes to handle the actual reading of tags
        pool = Pool()
        queue_size = self.read_queue.qsize()
        while self.read_queue.qsize() > 0:
            args_list = []
            # Get 100 songs from the queue
            for x in range(100):
                try:
                    args_list.append(self.read_queue.get(timeout=1))
                except:
                    break
            # Read the tags from the 100 songs and then stick the results in the
            # database queue.
            try:
                self.db_queue.put(pool.map(read_song, args_list))
                self.db_needs_updated.set()
            except:
                logger.error("Error processing read queue.")
            logger.debug("Processed %d items in %0.2f seconds" % (queue_size - self.read_queue.qsize(), time() - self.start_time))
        pool.close()
        pool.join()
        # Let the other processes know we're finished.
        while not self.db_queue.qsize() == 0:
            sleep(1)
        self.reading.clear()

    def clean(self):
        """Search music_path to find if any of the songs in records have been
        removed, and then remove them from couchdb.
        """
        self.cleaning.set()
        logger.debug("Searching for changed/removed files.")
        start_time = time()
        records = self.couchdb.view('songs/mtime')
        # Create a list of files that are missing and need to be removed and also
        # a dict that is going to hold all of the songs from the database whose
        # corresponding files still exist.
        remove = []
        songs = {}
        removed = 0
        for song in records:
            path = song['key']
            # Check if the file this database record points to is still there, and
            # add it to the list to be removed if it's not.
            if not os.path.isfile(path) or not path.startswith(self.music_path):
                remove.append(self.couchdb[song['id']])
                removed += 1
                # Once our list of songs to be removed hits 100, delete them all in
                # a batch. This is much quicker than doing them one at a time.
                if removed % 100 == 0:
                    self.couchdb.bulk_delete(remove)
                    remove = []
                    logger.debug("Removed %d songs in %0.2f seconds." % (removed, time() - start_time))
            else:
                # Add the song to the dict we're going to return
                songs[song['id']] = song['value']
        # We ran out of songs without hitting the magic number 100 to trigger a
        # batch delete, so let's get any stragglers now.
        self.couchdb.bulk_delete(remove)
        logger.debug("Removed %d songs in %0.2f seconds." % (removed, time() - start_time))
        self.cleaning.clear()
        return songs


def read_song(args):
    # Figure out which function we need to use to read the tags from this file
    # and then call it.
    try:
        if args[3] == 'wma':
            song = read_wma(args[0], args[1], args[2], args[4])
        else:
            song = read_metadata(args[0], args[1], args[2], args[4])
        # Return a tuple with the song metadata and whether this item was already
        # in the database.
        return song
    except:
        logger.error("Error processing %s" % args[0])
        return None 


def read_metadata(location, id, mtime, revision):
    """Uses Mutagen to read the metadata of a file and returns it as a dict"""
    # Try to open the file
    try:
        metadata = mutagen.File(location, None, True)
    except:
        logger.error("%s made Mutagen explode." % location)
        return None
    # Create the metadata object we're going to return
    song = {}
    # Set the '_id' property which CouchDB uses as a UUID
    song['_id'] = id
    song['location'] = location
    song['type'] = 'song'
    song['mtime'] = mtime
    song['tracknumber'] = 0
    if revision:
        song['_rev'] = revision
    # Try to set the length of the song in seconds, the bitrate in bps and the
    # mimetype and a default track number of the file.
    try:
        song['length'] = metadata.info.length
    except:
        song['length'] = 0
    try:
        song['bitrate'] = metadata.info.bitrate
    except:
        song['bitrate'] = 0
    try:
        song['mimetype'] = metadata.mime[0]
    except:
        pass
    # Create artist and album IDs which are just SHA-1 hashes of each field
    try:
        artist = metadata['artist'][0]
        song['artist_hash'] = hashlib.sha1(artist.encode('utf-8')).hexdigest()
    except:
        artist = "Unknown Artist"
        song['artist_hash'] = hashlib.sha1(artist.encode('utf-8')).hexdigest()
    try:
        album = metadata['album'][0]
        song['album_hash'] = hashlib.sha1(album.encode('utf-8')).hexdigest()
    except:
        album = "Unknown Album"
        song['album_hash'] = hashlib.sha1(album.encode('utf-8')).hexdigest()
    # Go through each tag we read from the file and add it to our ojbect.
    for tag, value in metadata.iteritems():
        try:
            # Mutagen returns all metadata as lists, so normally we'd just get
            # value[0], but 'genre' gets special treatment because we want to
            # save a list to the database. That way we can support multiple
            # genre tags.
            if tag == 'genre':
                song[tag] = value
            # Mutagen returns the tracknumber in a format like '2/12'. We're
            # only interested in the track number, not the total number of
            # tracks.
            elif tag == 'tracknumber':
                try:
                    song[tag] = int(value[0].split('/')[0])
                except:
                    song[tag] = 0
            # We need to ignore tags that contain cover art data so we don't
            # end up inserting giant binary blobs into our database.
            elif tag != 'coverart' and tag != 'APIC:':
                song[tag] = value[0]
        except TypeError:
            pass
        except AttributeError:
            pass
    return song


def read_wma(location, id, mtime, revision):
    """Uses Mutagen to read the metadata of a WMA file and returns it as a
    dict. WMA files need special treatment because unlike MP3 and MP4, Mutagen
    doesn't offer an 'easy' interface to get metadata from WMA files. So, where
    we'd normally get the album title like song['album'], with WMA we have to
    use song['WM/AlbumTitle']. So, we use dict called asf_map to map the WMA
    specific values to what we want them to be in the database.
    """
    # Try to open the file
    try:
        metadata = mutagen.File(location, None, True)
    except:
        logger.error("%s made Mutagen explode." % location)
        return None
    # Create the metadata object we're going to return
    song = {}
    # Set the '_id' property which CouchDB uses as a UUID
    song['_id'] = id
    song['location'] = location
    song['type'] = 'song'
    song['mtime'] = mtime
    song['tracknumber'] = 0
    if revision:
        song['_rev'] = revision
    # Try to set the length of the song in seconds, the bitrate in bps and the
    # mimetype of the file.
    try:
        song['length'] = metadata.info.length
    except:
        song['length'] = 0
    try:
        song['bitrate'] = metadata.info.bitrate
    except:
        song['bitrate'] = 0
    try:
        song['mimetype'] = metadata.mime[0]
    except:
        pass
    # Create artist and album IDs which are just SHA-1 hashes of each field
    try:
        artist = metadata['Author'][0]
        song['artist_hash'] = hashlib.sha1(artist.encode('utf-8')).hexdigest()
    except:
        artist = "Unknown Artist"
        song['artist_hash'] = hashlib.sha1(artist.encode('utf-8')).hexdigest()
    try:
        album = metadata['WM/AlbumTitle'][0]
        song['album_hash'] = hashlib.sha1(album.encode('utf-8')).hexdigest()
    except:
        album = "Unknown Album"
        song['album_hash'] = hashlib.sha1(album.encode('utf-8')).hexdigest()
    for tag, value in metadata.iteritems():
        try:
            # Mutagen returns all metadata as lists, so normally we'd just get
            # value[0], but 'genre' gets special treatment because we want to
            # save a list to the database. That way we can support multiple
            # genre tags.
            if tag == 'WM/Genre':
                song[asf_map[tag]] = []
                for genre in value:
                    song[asf_map[tag]].append(unicode(genre))
            # Mutagen returns the tracknumber in a format like '2/12'. We're
            # only interested in the track number, not the total number of
            # tracks.
            elif tag == 'WM/TrackNumber':
                try:
                    song[asf_map[tag]] = int(str(value[0]).split('/')[0])
                except:
                    song[asf_map[tag]] = 0
            # We need to ignore tags that contain cover art data so we don't
            # end up inserting giant binary blobs into our database.
            elif tag != 'WM/Picture':
                song[asf_map[tag]] = unicode(value[0])
        except TypeError:
            pass
        except AttributeError:
            pass
        except KeyError:
            # We encountered a tag that wasn't in asf_map. Print it out to the
            # console so that hopefully someone will tell us and we can add it.
            logger.warn("Skipping unrecognized tag %s with data %s in file %s" % (tag, value[0], location))
    return song


# This dict maps Windows Media tag names to ones we can actually use.
asf_map = {
    'Title': 'title',
    'WM/AlbumTitle': 'album',
    'WM/TrackNumber': 'tracknumber',
    'Author': 'artist',
    'WM/AlbumArtist': 'albumartist',
    'WM/Year': 'date',
    'WM/Genre': 'genre',
    'WM/AlbumArtistSortOrder': 'albumartistsort',
    'WM/ArtistSortOrder': 'artistsort',
    'MusicBrainz/Artist Id': 'musicbrainz_artistid',
    'MusicBrainz/Track Id': 'musicbrainz_trackid',
    'MusicBrainz/Album Id': 'musicbrainz_albumid',
    'MusicBrainz/Album Artist Id': 'musicbrainz_albumartistid',
    'MusicIP/PUID': 'musicip_puid',
    'MusicBrainz/Album Status': 'musicbrainz_albumstatus',
    'MusicBrainz/Album Type': 'musicbrainz_albumtype',
    'MusicBrainz/Album Release Country': 'releasecountry',
    'WM/Publisher': 'organization',
    'WM/PartOfSet': 'discnumber',
    'WM/OriginalReleaseYear': 'originaldate'
    }
