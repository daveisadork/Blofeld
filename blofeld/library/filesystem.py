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
from threading import Event, Thread

import mutagen
from mutagen.easyid3 import EasyID3

from blofeld.config import cfg
from blofeld.log import logger


class Scanner:
    def __init__(self, music_path, couchdb):
        self.music_path = music_path
        self.couchdb = couchdb
        # Create the shared objects our various threads and processes will be
        # using to communicate.
        self.read_queue = Queue()
        self.db_queue = Queue()
        self.scanning = Event()
        self.updating = Event()
        self.cleaning = Event()
        self.reading = Event()
        self.compacting = Event()
        self.db_working = Event()
        self.stopping = Event()
        self.finished = Event()
        self.jobs = {}
        self.current_job = None
        self.total_items = 0
        self.processed_items = 0

    def stop(self):
        if not self.stopping.is_set():
            logger.debug("Stopping the file scanner.")
            self.stopping.set()
        for timeout in range(10):
            if not self.updating.is_set():
                break
            sleep(1)
        if self.updating.is_set():
            logger.debug("Timed out waiting for file scanner to stop.")
        else:
            self.stopping.clear()
        if not self.stopping.is_set():
            logger.debug("File scanner has stopped.")

    def exit(self):
        if self.stopping.is_set() and self.updating.is_set():
            if self.scanning.is_set() and self.scan_thread.is_alive():
                self.pool.terminate()

    def update(self):
        """Initiates the process of updating the database by removing any 
        songs that have gone missing, adding new songs and updating changed
        songs.
        """
        if self.updating.is_set():
            logger.warn("Library update requested, but already updating.")
            return self.current_job
        self.updating.set()
        self.update_thread = Thread(target=self._update)
        ticket = hashlib.sha1(str(time())).hexdigest()
        self.jobs[ticket] = {
            'status': 'Initializing',
            'current_item': self.music_path,
            'removed_items': 0,
            'new_items': 0,
            'changed_items': 0,
            'unchanged_items': 0,
            'queued_items': 0,
            'processed_items': 0,
            'total_time': 0
            }
        self.current_job = ticket
        logger.info("Starting library update.")
        self.update_thread.start()
        return ticket
    
    def _update(self):
        self.start_time = time()
        # Clean the database of files that no longer exist and get a list 
        # of the remaining songs in the database.
        self._clean()
        # Create a queue of files from which we need to read metadata.
        self._scan()
        if self.read_queue.qsize() > 0:
            # Spawn a new thread to handle the queue of files that need read.
            self.read_thread = Thread(target=self._process_read_queue)
            self.read_thread.start()
            # Give the read_thread a chance to get going and then spawn a 
            # new thread to handle inserting metadata into the database.
            sleep(5)
            self.db_thread = Thread(target=self._add_items_to_db)
            self.db_thread.start()
            # Block while we wait for everything to finish
            self.db_working.wait(None)
            # Join our threads back
            self.read_thread.join()
            self.db_thread.join()
        self.jobs[self.current_job]['current_item'] = 'None'
        # Compact the database so it doesn't get unreasonably large. We do 
        # this in a separate thread so we can go ahead and return since the
        # we've added everything we need to the database already and we 
        # don't want to wait for this to finish.
        self.compact_thread = Thread(target=self._compact)
        self.compact_thread.start()
        self._compact()
        self.updating.clear()
        self.finished.set()
        finish_time = time() - self.start_time
        self.jobs[self.current_job]['status'] = 'Finished'
        self.jobs[self.current_job]['total_time'] = finish_time
        logger.debug("Added all new songs in %0.2f seconds." % finish_time)
        logger.info("Updated library in %0.2f seconds." % finish_time)

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

    def _compact(self):
        if self.stopping.is_set():
            return
        self.compacting.set()
        self.jobs[self.current_job]['status'] = 'Compacting the database'
        self.couchdb.compact()
        self.compacting.clear()

    def _scan(self):
        """Scans the music_path to find songs that need to be added to the
        database and adds those files to the read_queue.
        """
        if self.stopping.is_set():
            return
        logger.debug("Scanning for new files.")
        self.scanning.set()
        self.jobs[self.current_job]['status'] = 'Scanning for new files'
        self.jobs[self.current_job]['unchanged_items'] = 0
        # Iterate through all the folders and files in music_path
        for root, dirs, files in os.walk(self.music_path):
            if self.stopping.is_set():
                break
            for item in files:
                # Get the file extension, e.g. 'mp3' or 'flac', and see if 
                # it's in the list of extensions we're supposed to look for.
                extension = os.path.splitext(item)[1].lower()[1:]
                if extension in cfg['MUSIC_EXTENSIONS']:
                    # Get the full decoded path of the file. The decoding 
                    # part is important if the filename includes non-ASCII 
                    # characters.
                    location = os.path.join(root, item)
                    filename = os.path.split(location)[1]
                    self.jobs[self.current_job]['current_item'] = filename
                    # Generate a unique ID for this song by making a SHA-1 
                    # hash of its location.
                    id = hashlib.sha1(location.encode('utf-8')).hexdigest()
                    # Get the time that this file was last modified
                    mtime = os.stat(os.path.join(root, item))[8]
                    # Find out if this song is already in the database and 
                    # if so whether it has been modified since the last time 
                    # we scanned it.
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
                        self.read_queue.put((location, id, mtime, revision))
                    else:
                        self.jobs[self.current_job]['unchanged_items'] += 1
        self.jobs[self.current_job]['queued_items'] = self.read_queue.qsize()
        self.scanning.clear()
        if self.read_queue.qsize() < 1:
            logger.debug("No new files found.")
            return False
        logger.debug("Queued %d songs to be read." % self.read_queue.qsize())
        return True

    def _add_items_to_db(self):
        """Watches the db_queue for metadata from songs and inserts that data
        into the database.
        """
        # While the read queue is still being processed or we have stuff 
        # waiting to be added to the database...
        self.db_working.set()
        while self.reading.is_set() or self.db_queue.qsize() > 0 \
              and not self.stopping.is_set():
            if self.db_queue.qsize() > 0:
                songs = []
                while self.db_queue.qsize() > 0:
                    # Grab all the items out of the database queue
                    songs.extend(self.db_queue.get())
                updated = 0
                new = []
                for song in songs:
                    if not song:
                        # There must've been a problem reading this file so 
                        # we'll skip it.
                        continue
                    # Get the metadata ready to send to the database
                    new.append(song)
                    if "_rev" in song:
                        updated += 1
                    filename = os.path.split(song['location'])[1]
                    self.jobs[self.current_job]['current_item'] = filename
                # Make our changes to the database
                self.couchdb.bulk_save(new)
                new_items = len(new) - updated
                self.jobs[self.current_job]['new_items'] += new_items
                self.jobs[self.current_job]['changed_items'] += updated
                logger.debug("Added %d songs to the database, %d of which\
                             already existed." % (len(new), updated))
            sleep(5)
        self.db_working.clear()

    def _process_read_queue(self):
        """Spawns a pool of worker processes to handle reading the metadata
        from all of the files in the read_queue.
        """
        self.reading.set()
        status = 'Importing songs to the library'
        self.jobs[self.current_job]['status'] = status
        # Create a pool of processes to handle the actual reading of tags.
        # Using processes instead of threads lets us take full advantage of
        # multi-core CPUs so this operation doesn't take as long.
        self.pool = Pool()
        queue_size = self.read_queue.qsize()
        while self.read_queue.qsize() > 0 and not self.stopping.is_set():
            args_list = []
            # Get 100 songs from the queue
            for x in range(100):
                try:
                    args_list.append(self.read_queue.get(timeout=1))
                except:
                    break
            # Read the tags from the 100 songs and then stick the results in 
            # the database queue.
            try:
                self.db_queue.put(self.pool.map(read_metadata, args_list))
                n_items = len(args_list)
                self.jobs[self.current_job]['processed_items'] += n_items
            except:
                logger.error("Error processing read queue.")
            logger.debug("Processed %d items in %0.2f seconds" % 
                         (queue_size - self.read_queue.qsize(),
                         time() - self.start_time))
        self.pool.close()
        self.pool.join()
        self.reading.clear()

    def _clean(self):
        """Searches music_path to find if any of the songs in records have 
        been removed, and then remove them from couchdb.
        """
        if self.stopping.is_set():
            return
        self.cleaning.set()
        status = 'Searching for changed/removed files'
        self.jobs[self.current_job]['status'] = status
        logger.debug(status)
        start_time = time()
        records = self.couchdb.view('songs/mtime')
        # Create a list of files that are missing and need to be removed 
        # and also a dict that is going to hold all of the songs from the 
        # database whose corresponding files still exist.
        remove = []
        songs = {}
        removed = 0
        for song in records:
            if self.stopping.is_set():
                break
            path = song['key']
            filename = os.path.split(path)[1]
            self.jobs[self.current_job]['current_item'] = filename
            # Check if the file this database record points to is still 
            # there, and add it to the list to be removed if it's not.
            if not (os.path.isfile(path) or
                    path.startswith(self.music_path)):
                remove.append(self.couchdb[song['id']])
                removed += 1
                # Once our list of songs to be removed hits 100, delete 
                # them all in a batch. This is much quicker than doing them 
                # one at a time.
                if removed % 100 == 0:
                    self.couchdb.bulk_delete(remove)
                    self.jobs[self.current_job]['removed_items'] = removed
                    remove = []
                    logger.debug("Removed %d songs in %0.2f seconds." % 
                                 (removed, time() - start_time))
            else:
                # Add the song to the dict we're going to return
                songs[song['id']] = song['value']
        self.jobs[self.current_job]['current_item'] = 'None'
        # We ran out of songs without hitting the magic number 100 to  
        # trigger a batch delete, so let's get any stragglers now.
        self.couchdb.bulk_delete(remove)
        self.jobs[self.current_job]['removed_items'] = removed
        logger.debug("Removed %d songs in %0.2f seconds." % 
                     (removed, time() - start_time))
        self.records = songs
        self.cleaning.clear()


def read_metadata((location, id, mtime, revision)):
    """Read the metadata of a file and return it as a dict."""
    # Try to open the file and read its tags
    try:
        metadata = mutagen.File(location, None, True)
    except:
        logger.error("%s made Mutagen explode." % location)
        return None
    # Create the metadata object we're going to return with some default 
    # values filled in. This is just in case there aren't tags for these 
    # things so we don't run into problems elsewhere with this data not 
    # being there.
    song = {
        '_id': id,
        'location': location,
        'title': os.path.split(location)[1],
        'mtime': mtime,
        'artist': 'Unknown Artist',
        'album': 'Unknown Album',
        'genre': [],
        'date': '',
        'tracknumber': 0,
        'discnumber': 1,
        'bitrate': 0,
        'length': 0,
        'subtitle': '',
        'discsubtitle': '',
        'compilation': False,
        'replaygain_track_gain': None,
        'replaygain_album_gain': None,
        'replaygain_track_peak': None,
        'replaygain_album_peak': None,
        'type': 'song'
    }
    if revision:
        song['_rev'] = revision
    # Try to set the length of the song in seconds, the bitrate in bps and 
    # the mimetype and a default track number of the file.
    try:
        song['length'] = metadata.info.length
    except:
        pass
    try:
        song['bitrate'] = metadata.info.bitrate
    except:
        pass
    try:
        song['mimetype'] = metadata.mime[0]
    except:
        pass
    # Now we parse all the metadata and transfer it to our song object.
    if os.path.splitext(location)[1].lower()[1:] in ('wma', 'asf'):
        song = parse_wma(song, metadata)
    else:
        song = parse_metadata(song, metadata)
    # Fill in some needed tags if they're not present
    if not song.has_key('albumartist'):
        song['albumartist'] = song['artist']
    for field in ('title', 'artist', 'album', 'albumartist'):
        if not song.has_key('%ssort' % field):
            song['%ssort' % field] = song[field]
    # Create artist and album IDs which are just SHA-1 hashes of each field
    for field in ('artist', 'album'):
        value = song[field].encode('utf-8')
        song['%s_hash' % field] = hashlib.sha1(value).hexdigest()
    return song


def parse_metadata(song, metadata):
    """Parses a Mutagen metadata object and transfers the data to a song 
    object that is suitable to insert into our database.
    """
    for tag, value in metadata.iteritems():
        try:
            # Mutagen returns all metadata as lists, so normally we'd just 
            # get value[0], but 'genre' and 'mood' get special treatment 
            # because we want to save a list to the database. That way we 
            # can support multiple genre/mood tags.
            if tag in ('genre', 'mood'):
                song[tag] = value
            # Sometimes tracknumbers are packed along with the totaltracks
            # using a '/', e.g. 2/11 and sometimes it's just the tracknumber.
            # We need to account for both cases.
            elif tag in ['track', 'tracknumber']:
                try:
                    tracknumber, totaltracks = str(value[0]).split('/')
                    song['tracknumber'] = int(tracknumber)
                    song['totaltracks'] = int(totaltracks)
                    song['tracktotal'] = int(totaltracks)
                except:
                    song[tag] = int(value[0])
            elif tag in ['totaltracks', 'tracktotal']:
                song['totaltracks'] = int(value[0])
                song['tracktotal'] = int(value[0])
            # Disc numbers work the same way as track numbers.
            elif tag in ['disc', 'discnumber']:
                try:
                    discnumber, totaldiscs = str(value[0]).split('/')
                    song['discnumber'] = int(discnumber)
                    song['totaldiscs'] = int(totaldiscs)
                    song['disctotal'] = int(totaldiscs)
                except:
                    song[tag] = int(value[0])
            elif tag in ['totaldiscs', 'disctotal']:
                song['totaldiscs'] = int(value[0])
                song['disctotal'] = int(value[0])
            elif tag == 'compilation':
                song[tag] = bool(int(value[0]))
            elif tag in ['replaygain_album_peak', 'replaygain_track_peak']:
                song[tag] = float(value[0])
            # We need to ignore tags that contain cover art data so we don't
            # end up inserting giant binary blobs into our database.
            elif tag in ['coverart', 'covr', 'APIC:', 
                         'metadata_block_picture', 'pictures', 'WM/Picture']:
                continue
            else:
                song[tag] = value[0]
        except TypeError:
            pass
        except AttributeError:
            pass
    return song


def parse_wma(song, metadata):
    """Parses a Mutagen WMA metadata object and transfers that data to a song
    object using a dict to map the WMA tag names to ones that we want them to
    be. This is a specialized version of parse_metadata().
    """
    for tag, value in metadata.iteritems():
        try:
            # Mutagen returns all metadata as lists, so normally we'd just 
            # get value[0], but 'genre' and 'mood' get special treatment 
            # because we want to save a list to the database. That way we 
            # can support multiple genre/mood tags.
            if tag in ('WM/Genre', 'WM/Mood'):
                song[asf_map[tag]] = []
                for genre in value:
                    song[asf_map[tag]].append(genre.value)
            # Sometimes tracknumbers are packed along with the totaltracks
            # using a '/', e.g. 2/11 and sometimes it's just the tracknumber.
            # We need to account for both cases.
            elif tag == 'WM/TrackNumber':
                try:
                    tracknumber, totaltracks = str(value[0].value).split('/')
                    song['tracknumber'] = int(tracknumber)
                    song['totaltracks'] = int(totaltracks)
                    song['tracktotal'] = int(totaltracks)
                except:
                    song['tracknumber'] = int(value[0].value)
            # Disc numbers work the same way as track numbers.
            elif tag == 'WM/PartOfSet':
                try:
                    discnumber, totaldiscs = str(value[0].value).split('/')
                    song['discnumber'] = int(discnumber)
                    song['totaldiscs'] = int(totaldiscs)
                    song['disctotal'] = int(totaldiscs)
                except:
                    song['discnumber'] = int(value[0].value)
            elif tag == 'TotalTracks':
                song['tracktotal'] = int(value[0].value)
                song['totaltracks'] = int(value[0].value)
            elif tag in ('foobar2000/TOTALDISCS', 'TotalDiscs'):
                song['disctotal'] = int(value[0].value)
                song['totaldiscs'] = int(value[0].value)
            elif tag == 'WM/IsCompilation':
                song['compilation'] = bool(value[0])
            elif tag in ['replaygain_album_peak', 'replaygain_track_peak']:
                song[tag] = float(value[0])
            # We need to ignore tags that contain cover art data so we don't
            # end up inserting giant binary blobs into our database.
            elif tag == 'WM/Picture':
                continue
            else:
                if type(value[0]) is unicode:
                    song[asf_map[tag]] = value[0]
                else:
                    song[asf_map[tag]] = value[0].value
        except TypeError:
            pass
        except AttributeError:
            pass
        except KeyError:
            # We encountered a tag that wasn't in asf_map. Print it out to 
            # the console so that hopefully someone will tell us and we can
            # add it.
            try:
                logger.warn("Skipping unrecognized tag %s with data %s in \
                            file %s" % (tag, value[0], song['location']))
            except:
                logger.warn("Skipping unrecognized tag %s with un-printable \
                            data in file %s" % (tag, song['location']))
    if not song.has_key('albumartist'):
        song['albumartist'] = song['artist']
    return song


# Register some tags we need that Mutagen doesn't already map.
EasyID3.RegisterTextKey('albumartist', 'TPE2')
EasyID3.RegisterTXXXKey('albumartistsort', 'ALBUMARTISTSORT')


# This dict maps Windows Media tag names to ones we can actually use.
asf_map = {
'Acoustid/Id': 'acoustid_id',
    'Author': 'artist',
    'Copyright': 'copyright',
    'LICENSE': 'license',
    'MusicBrainz/ASIN': 'asin',
    'MusicBrainz/Album Artist Id': 'musicbrainz_albumartistid',
    'MusicBrainz/Album Comment': 'musicbrainz_albumcomment',
    'MusicBrainz/Album Id': 'musicbrainz_albumid',
    'MusicBrainz/Album Release Country': 'releasecountry',
    'MusicBrainz/Album Status': 'musicbrainz_albumstatus',
    'MusicBrainz/Album Type': 'musicbrainz_releasetype',
    'MusicBrainz/Artist Id': 'musicbrainz_artistid',
    'MusicBrainz/Disc Id': 'musicbrainz_discid',
    'MusicBrainz/Release Group Id': 'musicbrainz_releasegroupid',
    'MusicBrainz/TRM Id': 'musicbrainz_trmid',
    'MusicBrainz/Track Id': 'musicbrainz_trackid',
    'MusicBrainz/Work Id': 'musicbrainz_workid',
    'MusicIP/PUID': 'musicip_puid',
    'Title': 'title',
    'TotalDiscs': 'totaldiscs',
    'TotalTracks': 'totaltracks',
    'WM/AlbumArtist': 'albumartist',
    'WM/AlbumArtistSortOrder': 'albumartistsort',
    'WM/AlbumSortOrder': 'albumsort',
    'WM/AlbumTitle': 'album',
    'WM/ArtistSortOrder': 'artistsort',
    'WM/Barcode': 'barcode',
    'WM/BeatsPerMinute': 'bpm',
    'WM/CatalogNo': 'catalognumber',
    'WM/Comments': 'comment:description',
    'WM/Composer': 'composer',
    'WM/Conductor': 'conductor',
    'WM/ContentGroupDescription': 'grouping',
    'WM/EncodedBy': 'encodedby',
    'WM/Genre': 'genre',
    'WM/ISRC': 'isrc',
    'WM/IsCompilation': 'compilation',
    'WM/Language': 'language',
    'WM/Lyrics': 'lyrics:description',
    'WM/Media': 'media',
    'WM/ModifiedBy': 'remixer',
    'WM/Mood': 'mood',
    'WM/OriginalReleaseYear': 'originaldate',
    'WM/PartOfSet': 'discnumber',
    'WM/Producer': 'producer',
    'WM/Publisher': 'label',
    'WM/Script': 'script',
    'WM/SetSubTitle': 'discsubtitle',
    'WM/SharedUserRating': '_rating',
    'WM/SubTitle': 'subtitle',
    'WM/TitleSortOrder': 'titlesort',
    'WM/TrackNumber': 'tracknumber',
    'WM/Writer': 'lyricist',
    'WM/Year': 'date',
    'beets/Album Artist Credit': 'albumartist_credit',
    'beets/Artist Credit': 'artist_credit',
    'foobar2000/TOTALDISCS': 'totaldiscs',
    'replaygain_album_gain': 'replaygain_album_gain',
    'replaygain_album_peak': 'replaygain_album_peak',
    'replaygain_track_gain': 'replaygain_track_gain',
    'replaygain_track_peak': 'replaygain_track_peak',
}
