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

import sys
import hashlib
import urllib
from urlparse import urlparse

try:
    from xml.etree.cElementTree import ElementTree
except:
    from xml.etree.ElementTree import ElementTree


def load_rhythmbox_db(rhythmdb, couchdb):
    """Parses the Rhythmbox XML database file rhythmdb and adds all of the
    songs in it to couchdb
    """
    logger.debug("Importing Rhythmbox database")
    # Create an ElementTree containing everything from the Rhythmbox database
    tree = ElementTree()
    tree.parse(rhythmdb)
    _entries = tree.findall("entry")
    # This object is going to hold all the songs we import.
    songs = {}
    for entry in _entries:
        # Make sure this entry is a song and create an object to store its
        # metadata.
        if entry.attrib['type'] == "song":
            song = {}
            song['type'] = 'song'
            # Go through all the tags for this song in the Rhythmbox DB and add
            # them to our object.
            for element in entry:
                # Get the name of the current tag
                tag = element.tag
                if tag == 'track-number':
                    try:
                        song['tracknumber'] = element.text
                    except:
                        song['tracknumber'] = ''
                # Rhythmbox doesn't support multiple genres, but we do so we
                # need the genre tag to be a list.
                elif tag == 'genre':
                    song['genre'] = []
                    try:
                        song['genre'].append(element.text)
                    except:
                        pass
                # 'location' is the URI for the file associated with this song.
                # We want to add a path to the database, not a URI.
                elif tag == 'location':
                    # URI seperators will always be '/' but the separator the
                    # current OS uses might be '\'. url2pathname will make sure
                    # everything is right and get rid of all the URL encoding
                    # (e.g. '%20' instead of ' ').
                    uri = urllib.url2pathname(element.text)
                    # Make sure we decode this path properly, otherwise
                    # urlparse will explode.
                    uri = uri.decode(sys.getfilesystemencoding())
                    # Now we use urlparse to split the URI into its scheme (the
                    # 'file://' part) and its path (the part we want), which we
                    # then save in our metadata object.
                    path = urlparse(uri).path
                    song['location'] = path
                # For 'artist' and 'album', we can just save the tag into our
                # object but then we need to make a SHA-1 hash for the ID and
                # save that. It has to be encoded as utf-8 or hashlib will
                # explode on non-ascii characters.
                elif tag == "artist":
                    song[tag] = element.text
                    artist_hash = hashlib.sha1(song[tag].encode("utf-8")).hexdigest()
                    song['artist_hash'] = artist_hash
                elif tag == "album":
                    song[tag] = element.text
                    album_hash = hashlib.sha1(song[tag].encode("utf-8")).hexdigest()
                    song['album_hash'] = album_hash
                # If the tag doesn't need any special treatment, add it right
                # into the metadata object.
                else:
                    try:
                        song[tag] = element.text
                    except:
                        song[tag] = ''
                    finally:
            # We need to make a SHA-1 hash of the location of this file, which
            # CouchDB will use as its UUID. The location needs to be utf-8
            # encoded or hashlib will explode with non-ascii characters. Then
            # we can add this song to our dict of all the songs.
            song['_id'] = hashlib.sha1(song['location'].encode('utf-8')).hexdigest()
            songs[song['_id']] = song
    # Figure out which songs have been removed or changed and remove them Then
    # save all the new or changed songs. We do all this at once since we can
    # parse rhythmbdb.xml and then bulk update everything at once in just a few
    # seconds.
    remove = find_removed_songs(couchdb, songs, couchdb.view('songs/all'))
    couchdb.bulk_delete(remove)
    couchdb.bulk_save(songs.values())


def find_removed_songs(couchdb, rhythmdb, records):
    """Creates a list of songs that exist in couchdb but don't exist (or have
    changed) in rhythmdb, and therefore need to be removed.
    """
    # Make a list to hold everything we want to remove
    remove = []
    for record in records:
        if record['id'] not in rhythmdb:
            remove.append(couchdb[record['id']])
        # Since Rhythmbox stores file modification times, we can find out if
        # a particular song has changed since the last time we imported.
        elif record['value']['mtime'] != rhythmdb[record['id']]['mtime']:
            remove.append(couchdb[record['id']])
        # If the song is in couchdb and in rhythmdb and hasn't changed, we
        # don't want to do anything with it, so remove it from the dict with
        # all the songs. If we don't do this, couchdbkit will explode when we
        # try to add it to the database since it already exists.
        else:
            del rhythmdb[record['id']]
    return remove

