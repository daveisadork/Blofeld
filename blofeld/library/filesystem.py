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
    records = remove_missing_files(music_path, couchdb, couchdb.view('songs/mtime'))
    start_time = time()
    print "Scanning for new files..."
    remove = []
    songs = []
    changed = 0
    unchanged = 0
    for root, dirs, files in os.walk(music_path):
        for item in files:
            extension = os.path.splitext(item)[1].lower()[1:]
            if extension in ACCEPTED_EXTENSIONS:
                location = os.path.join(root, item).decode(ENCODING)
                id = hashlib.sha1(location.encode('utf-8')).hexdigest()
                mtime = str(os.stat(os.path.join(root, item))[8])
                try:
                    record_mtime = records[id]
                except:
                    record_mtime = None
                if mtime != record_mtime:
                    song = read_metadata(root, item, location, id, mtime)
                    songs.append(song)
                    if id in records:
                        try:
                            remove.append(couchdb[id])
                        except:
                            pass
                    changed += 1
                    if changed % 100 == 0 and changed > 0:
                        couchdb.bulk_delete(remove)
                        couchdb.bulk_save(songs)
                        remove = []
                        songs = []
                        print "Added", changed, "songs in", \
                               time() - start_time, "seconds."
                else:
                    unchanged += 1
    couchdb.bulk_delete(remove)
    couchdb.bulk_save(songs)
    print "Added or updated", changed, "songs and skipped", unchanged, "in", \
           time() - start_time, "seconds."


def remove_missing_files(music_path, couchdb, records):
    start_time = time()
    print "Removing missing files..."
    remove = []
    songs = {}
    removed = 0
    for song in records:
        if not os.path.isfile(song['key']):
            remove.append(couchdb[song['id']])
            removed += 1
            if removed % 100 == 0:
                couchdb.bulk_delete(remove)
                remove = []
                print "Removed", removed, "songs in", time() - start_time, \
                      "seconds."
        else:
            songs[song['id']] = song['value']
    couchdb.bulk_delete(remove)
    print "Finished removing", removed, "songs in", time() - start_time, \
          "seconds."
    return songs


def read_metadata(root, item, location, id, mtime):
    metadata = mutagen.File(os.path.join(root, item), None, True)
    song = {}
    song['_id'] = id
    song['location'] = location
    song['type'] = 'song'
    song['mtime'] = mtime
    try: song['length'] = metadata.info.length
    except: song['length'] = 0
    try: song['bitrate'] = metadata.info.bitrate
    except: song['bitrate'] = 0
    try: song['mimetype'] = metadata.mime[0]
    except: pass
    try:
        song['artist_hash'] = hashlib.sha1(metadata['artist'][0].encode('utf-8')).hexdigest()
    except:
        song['artist_hash'] = hashlib.sha1("Unknown Artist").hexdigest()
    try:
        song['album_hash'] = hashlib.sha1(metadata['album'][0].encode('utf-8')).hexdigest()
    except:
        song['album_hash'] = hashlib.sha1("Unknown Album").hexdigest()
    for tag, value in metadata.iteritems():
        try:
            if tag == 'genre':
                song[tag] = value
            elif tag == 'tracknumber':
                try:
                    song[tag] = int(value[0].split('/')[0])
                except:
                    song[tag] = 0
            elif tag != 'coverart' and tag != 'APIC:':
                song[tag] = value[0]
        except TypeError:
            pass
        except AttributeError:
            pass
    return song

