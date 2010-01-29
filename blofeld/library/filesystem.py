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

import sys
import os
import locale
import urllib
import hashlib
import locale

import mutagen
from couchdb.client import Document

try:
    from xml.etree.cElementTree import ElementTree
except:
    from xml.etree.ElementTree import ElementTree

def load_music_from_dir(music_path):
    songs = {}
    for root, dirs, files in os.walk(music_path):
        for item in files:
            for ext in ['.mp3', '.ogg', '.m4a', '.flac', '.mp2', '.wma']:
                if ext in item.lower():
                    song = read_metadata(root, item)
                    songs[song['_id']] = song
    return songs

def read_metadata(root, item):
    metadata = mutagen.File(os.path.join(root, item), None, True)
    song = Document()
    location = "file://" + os.path.join(root, item)
    song['_id'] = hashlib.sha1(location).hexdigest()
    song['location'] = unicode(location.decode('utf-8'))
    song['type'] = 'song'
    try:
        song['artist_hash'] = hashlib.sha1(metadata['artist'][0]).hexdigest()
    except:
        song['artist_hash'] = hashlib.sha1("Unknown Artist").hexdigest()
    try:
        song['album_hash'] = hashlib.sha1(metadata['album'][0]).hexdigest()
    except:
        song['album_hash'] = hashlib.sha1("Unknown Album").hexdigest()
    try:
        for tag, value in metadata.iteritems():
            if tag == 'genre':
                song[tag] = value
            elif tag == 'tracknumber':
                try:
                    song[tag] = value[0].split('/')[0]
                except:
                    song[tag] = ''
            elif tag != 'coverart' and tag != 'APIC:':
                song[tag] = value[0]
    except TypeError:
        pass
    except AttributeError:
        pass
    return song

#def get_metadata(filename, player):
#    """Try to extract any tags from a file that we can"""
#    player.liststore.clear()
#    player.treeview.set_headers_visible(False)
#    player.filechooserbutton.set_filename(filename)
#    enc = locale.getpreferredencoding()
#    try: 
#        metadata = mutagen.File(filename, None, True)
##        output = open("/home/dhayes/Desktop/output.txt", 'w')
##        output.write(metadata.pprint().encode(enc, 'replace'))
#        for tag, value in metadata.iteritems():
#            if tag != 'coverart' and tag != 'APIC:':
#                try:
#                    for data in value:
#                        player.liststore.append([str(tag), str(data)])
#                except:
#                    player.liststore.append([str(tag), str(value)])
#        player.treeview.set_headers_visible(True)
#        get_cover(metadata, player)
#    except AttributeError:
#        player.liststore.append(["That's not a music file!", ""])
#    except KeyboardInterrupt: raise
#    except TypeError:
#        player.liststore.append(["One file at a time, junior.", ""])
#    except IOError:
#        player.liststore.append(["A folder? Just who do you think you are?", ""])
#    except Exception, err: player.liststore.append([str(err), ""])

#def load_rhythmbox_db(path):
#    tree = ElementTree()
#    tree.parse(path)
#    _entries = tree.findall("entry")
#    songs = {}
#    artists = {}
#    albums = {}
#    relationships = {}
#    for entry in _entries:
#        if entry.attrib['type'] == "song":
#            location_hash = hashlib.sha1(entry.find('location').text.encode("utf-8")).hexdigest()
#            songs[location_hash] = {}
#            for element in entry:
#                tag = element.tag
#                try:
#                    songs[location_hash][tag] = element.text
#                except:
#                    songs[location_hash][tag] = ''
#                finally:
#                    if tag == "artist":
#                        artist_hash = hashlib.sha1(songs[location_hash][tag].encode("utf-8")).hexdigest()
#                        songs[location_hash]['artist_hash'] = artist_hash
#                        if artist_hash not in artists:
#                            artists[artist_hash] = songs[location_hash][tag]
#                    if tag == "album":
#                        album_hash = hashlib.sha1(songs[location_hash][tag].encode("utf-8")).hexdigest()
#                        songs[location_hash]['album_hash'] = album_hash
#                        if album_hash not in albums:
#                            albums[album_hash] = songs[location_hash][tag]
#    for song_hash in songs:
#        artist_hash = songs[song_hash]['artist_hash']
#        album_hash= songs[song_hash]['album_hash']
#        if artist_hash not in relationships:
#            relationships[artist_hash] = {}
#        if album_hash not in relationships[artist_hash]:
#            relationships[artist_hash][album_hash] = []
#        relationships[artist_hash][album_hash].append(song_hash)
#    return (artists, albums, songs, relationships)

