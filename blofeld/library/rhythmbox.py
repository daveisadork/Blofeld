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
import urllib

try:
    from xml.etree.cElementTree import ElementTree
except:
    from xml.etree.ElementTree import ElementTree

def load_rhythmbox_db(rhythmdb, couchdb):
    "Importing Rhythmbox database"
    tree = ElementTree()
    tree.parse(rhythmdb)
    _entries = tree.findall("entry")
    songs = {}
    for entry in _entries:
        if entry.attrib['type'] == "song":
            song = {}
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
                elif tag == 'location':
                    song['location'] = urllib.url2pathname(entry.find('location').text).decode('utf-8')
                else:
                    try:
                        song[tag] = element.text
                    except:
                        song[tag] = ''
                    finally:
                        if tag == "artist":
                            artist_hash = hashlib.sha1(song[tag].encode("utf-8")).hexdigest()
                            song['artist_hash'] = artist_hash
                        if tag == "album":
                            album_hash = hashlib.sha1(song[tag].encode("utf-8")).hexdigest()
                            song['album_hash'] = album_hash
            song['_id'] = hashlib.sha1(song['location'].encode('utf-8')).hexdigest()
            songs[song['_id']] = song
    remove = find_removed_songs(couchdb, songs, couchdb.view('songs/all'))
    couchdb.bulk_delete(remove)
    couchdb.bulk_save(songs.values())


def find_removed_songs(couchdb, rhythmdb, records):
    remove = []
    for record in records:
        if record['id'] not in rhythmdb:
            remove.append(couchdb[record['id']])
        elif record['value']['mtime'] != rhythmdb[record['id']]['mtime']:
            remove.append(couchdb[record['id']])
        else:
            del rhythmdb[record['id']]
    return remove
