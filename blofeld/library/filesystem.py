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

import os
import hashlib
from time import time
import urllib

import mutagen

from blofeld.config import *


def load_music_from_dir(music_path, couchdb):
    """Scans music_path for songs, adds new/changed songs to couchdb and
    removes any songs that have gone missing.
    """
    # Clean the database of files that no longer exist and get a list of the
    # remaining songs in the database.
    records = remove_missing_files(music_path, couchdb, couchdb.view('songs/mtime'))
    start_time = time()
    print "Scanning for new files..."
    # Create lists to contain songs we need to remove and save
    remove = []
    songs = []
    changed = 0
    unchanged = 0
    # Iterate through all the folders and files in music_path
    for root, dirs, files in os.walk(music_path):
        for item in files:
            # Get the file extension, e.g. 'mp3' or 'flac', and see if it's in
            # the list of extensions we're supposed to look for.
            extension = os.path.splitext(item)[1].lower()[1:]
            if extension in ACCEPTED_EXTENSIONS:
                # Get the full decoded path of the file. The decoding part is
                # important if the filename includes non-ASCII characters.
                location = os.path.join(root, item).decode(ENCODING)
                # Generate a unique ID for this song by making a SHA-1 hash of
                # its location.
                id = hashlib.sha1(location.encode('utf-8')).hexdigest()
                # Get the time that this file was last modified
                mtime = str(os.stat(os.path.join(root, item))[8])
                # Find out if this song is already in the database and if so
                # whether it has been modified since the last time we scanned
                # it.
                try:
                    record_mtime = records[id]
                except:
                    record_mtime = None
                if mtime != record_mtime:
                    # WMA files get special treatment. See read_wma() for more
                    # information on why.
                    if extension == 'wma':
                        song = read_wma(location, id, mtime)
                    else:
                        song = read_metadata(location, id, mtime)
                    if song:
                        # Add the song to the list
                        songs.append(song)
                        # If the song is already in the database, add it to the
                        # removal list.
                        if id in records:
                            try:
                                remove.append(couchdb[id])
                            except:
                                pass
                        changed += 1
                        # If we have 100 songs ready to add to the database,
                        # remove the ones that are already existing (since I
                        # don't know how to update them in place) and then add
                        # the 100 songs in the list. Doing this in 100 song
                        # chunks like this is much quicker than doing them one
                        # at a time.
                        if changed % 100 == 0 and changed > 0:
                            couchdb.bulk_delete(remove)
                            couchdb.bulk_save(songs)
                            remove = []
                            songs = []
                            print "Added", changed, "songs in", \
                                   time() - start_time, "seconds."
                else:
                    unchanged += 1
    # We ran out of files to scan without hitting that magic number 100 to do
    # the database update, so let's go ahead and get whatever's left.
    couchdb.bulk_delete(remove)
    couchdb.bulk_save(songs)
    print "Added or updated", changed, "songs and skipped", unchanged, "in", \
           time() - start_time, "seconds."


def remove_missing_files(music_path, couchdb, records):
    """Search music_path to find if any of the songs in records have been 
    removed, and then remove them from couchdb.
    """
    start_time = time()
    print "Removing missing files..."
    # Create a list of files that are missing and need to be removed and also
    # a dict that is going to hold all of the songs from the database whose
    # corresponding files still exist.
    remove = []
    songs = {}
    removed = 0
    for song in records:
        # Check if the file this database record points to is still there, and
        # add it to the list to be removed if it's not.
        if not os.path.isfile(song['key']):
            remove.append(couchdb[song['id']])
            removed += 1
            # Once our list of songs to be removed hits 100, delete them all in
            # a batch. This is much quicker than doing them one at a time.
            if removed % 100 == 0:
                couchdb.bulk_delete(remove)
                remove = []
                print "Removed", removed, "songs in", time() - start_time, \
                      "seconds."
        else:
            # Add the song to the dict we're going to return
            songs[song['id']] = song['value']
    # We ran out of songs without hitting the magic number 100 to trigger a
    # batch delete, so let's get any stragglers now.
    couchdb.bulk_delete(remove)
    print "Finished removing", removed, "songs in", time() - start_time, \
          "seconds."
    return songs


def read_metadata(location, id, mtime):
    """Uses Mutagen to read the metadata of a file and returns it as a dict"""
    # Try to open the file
    try:
        metadata = mutagen.File(location, None, True)
    except:
        print location, "made Mutagen explode."
        return None
    # Create the metadata object we're going to return
    song = {}
    # Set the '_id' property which CouchDB uses as a UUID
    song['_id'] = id
    song['location'] = location
    song['type'] = 'song'
    song['mtime'] = mtime
    # Try to set the length of the song in seconds, the bitrate in bps and the
    # mimetype of the file.
    try: song['length'] = metadata.info.length
    except: song['length'] = 0
    try: song['bitrate'] = metadata.info.bitrate
    except: song['bitrate'] = 0
    try: song['mimetype'] = metadata.mime[0]
    except: pass
    # Create artist and album IDs which are just SHA-1 hashes of each field
    try:
        artist = metadata['artist'][0]
        song['artist_hash'] = hashlib.sha1(artist.encode('utf-8')).hexdigest()
    except:
        song['artist_hash'] = hashlib.sha1("Unknown Artist").hexdigest()
    try:
        metadata['album'][0]
        song['album_hash'] = hashlib.sha1(album.encode('utf-8')).hexdigest()
    except:
        song['album_hash'] = hashlib.sha1("Unknown Album").hexdigest()
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


def read_wma(location, id, mtime):
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
        print location, "made Mutagen explode."
        return None
    # Create the metadata object we're going to return
    song = {}
    # Set the '_id' property which CouchDB uses as a UUID
    song['_id'] = id
    song['location'] = location
    song['type'] = 'song'
    song['mtime'] = mtime
    # Try to set the length of the song in seconds, the bitrate in bps and the
    # mimetype of the file.
    try: song['length'] = metadata.info.length
    except: song['length'] = 0
    try: song['bitrate'] = metadata.info.bitrate
    except: song['bitrate'] = 0
    try: song['mimetype'] = metadata.mime[0]
    except: pass
    # Create artist and album IDs which are just SHA-1 hashes of each field
    try:
        artist = metadata['Author'][0]
        song['artist_hash'] = hashlib.sha1(artist.encode('utf-8')).hexdigest()
    except:
        song['artist_hash'] = hashlib.sha1("Unknown Artist").hexdigest()
    try:
        album = metadata['WM/AlbumTitle'][0]
        song['album_hash'] = hashlib.sha1(album.encode('utf-8')).hexdigest()
    except:
        song['album_hash'] = hashlib.sha1("Unknown Album").hexdigest()
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
            print "Skipping unrecognized tag", tag, "with data", value[0]
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
    'WM/PartOfSet': 'discnumber'
    }
