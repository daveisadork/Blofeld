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

import hashlib

from couchdb.client import Document
try:
    from xml.etree.cElementTree import ElementTree
except:
    from xml.etree.ElementTree import ElementTree

def load_rhythmbox_db(path):
    "Importing Rhythmbox database"
    tree = ElementTree()
    tree.parse(path)
    _entries = tree.findall("entry")
    songs = {}
#    artists = {}
#    albums = {}
#    relationships = {}
    for entry in _entries:
        if entry.attrib['type'] == "song":
            song = Document()
            song['_id'] = hashlib.sha1(entry.find('location').text.encode("utf-8")).hexdigest()
            song['type'] = 'song'
            for element in entry:
                tag = element.tag
                if tag == 'track-number':
                    try:
                        song['tracknumber'] = element.text
                    except:
                        song['tracknumber'] = ''
                elif tag == 'genre':
                    song['genre'] = []
                    try:
                        song['genre'].append(element.text)
                    except:
                        pass
                else:
                    try:
                        song[tag] = element.text
                    except:
                        song[tag] = ''
                    finally:
                        if tag == "artist":
                            artist_hash = hashlib.sha1(song[tag].encode("utf-8")).hexdigest()
                            song['artist_hash'] = artist_hash
#                            if artist_hash not in artists:
#                                artists[artist_hash] = song[tag]
                        if tag == "album":
                            album_hash = hashlib.sha1(song[tag].encode("utf-8")).hexdigest()
                            song['album_hash'] = album_hash
#                            if album_hash not in albums:
#                                albums[album_hash] = song[tag]
            songs[song['_id']] = song
#    for song_hash in songs:
#        artist_hash = songs[song_hash]['artist_hash']
#        album_hash= songs[song_hash]['album_hash']
#        if artist_hash not in relationships:
#            relationships[artist_hash] = {}
#        if album_hash not in relationships[artist_hash]:
#            relationships[artist_hash][album_hash] = []
#        relationships[artist_hash][album_hash].append(song_hash)
#    return (artists, albums, songs, relationships)
    return songs

