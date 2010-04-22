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


import cStringIO as StringIO
import cherrypy
try:
    import xml.etree.cElementTree as ElementTree
except:
    import xml.etree.ElementTree as ElementTree


def json_to_playlist(base_url, songs, output='xspf', format=None, bitrate=None):
    """Converts a JSON object or Dictionary into a playlist file of some kind.
    The possible target formats are PLS, M3U and the default which is XSPF.
    """
    # Create a file object in memory to write the playlist into
    playlist = StringIO.StringIO()
    # If the client asked for specific formats, make them into a string we can
    # stick on the end of all the URIs as post variables.
    if not format:
        format = ''
    else:
        format = '&format=' + format
    if not bitrate:
        bitrate = ''
    else:
        bitrate = '&bitrate=' + format
    if output == 'm3u':
        # Set the content type
        ct = 'audio/x-mpegurl'
        # Write the header specifying an M3U file
        playlist.write('#EXTM3U\n')
        # Add each song to the playlist
        for song in songs:
            # The 'info' line needs to start with the integer length of the
            # song in seconds followed by the title. So first, round the length
            # down (in case it's a floating point number) and convert it to
            # an int. Then we add it into the info string.
            length = int(round(song['length']))
            info =  str(length) + "," + song['artist'] + " - " + song['title']
            uri = base_url + '/get_song?songid=' + song['id'] + format + bitrate
            playlist.write('\n#EXTINF:' + info.encode('utf-8') + '\n')
            playlist.write(uri + "\n")
    elif output == 'pls':
        # Set the content type
        ct = 'audio/x-scpls'
        # PLS playlists use a number appended to the end of each variable name
        # to differentiate between playlist entries, e.g. File0, File1, etc.
        # Here, we create a counter that we can append to each of our variable
        # names as we add entries to the playlist.
        counter = 1
        # Write the header specifying a PLS file and the number of songs in
        # this playlist.
        playlist.write('[playlist]\n')
        playlist.write('\nNumberOfEntries=' + str(len(songs)) + '\n')
        for song in songs:
            uri = base_url + '/get_song?songid=' + song['id'] + format + bitrate
            playlist.write('\nFile' + str(counter) + '=' + uri)
            playlist.write('\nTitle' + str(counter) + '=' + song['artist'].encode('utf-8') + \
                           " - " + song['title'].encode('utf-8'))
            # 'Length' needs to be a nonzero positive integer or -1 for unknown
            if int(round(song['length'])) == 0:
                length = '-1'
            else:
                length = str(int(round(song['length'])))
            playlist.write('\nLength' + str(counter) + '=' + length + '\n')
            counter += 1
        playlist.write('\nVersion=2\n')
    elif output == 'xspf':
        # Set the content type
        ct = 'application/xspf+xml'
        # Create a root Element <playlist> and give it a child element
        # <tracklist> which will contain all the songs.
        root = ElementTree.Element('playlist', version='1',
                                   xmlns='http://xspf.org/ns/0/')
        tracklist = ElementTree.SubElement(root, 'tracklist')
        for song in songs:
            # Since XSPF supports cover art, generate a URI for the cover image
            # as well as the song.
            song_uri = base_url + '/get_song?songid=' + song['id'] + format + bitrate
            cover_uri = base_url + '/get_cover?size=500&songid=' + song['id']
            # Create the <track> element and add all the relevent tags as 
            # children.
            track = ElementTree.SubElement(tracklist, 'track')
            ElementTree.SubElement(track, 'title').text = song['title']
            ElementTree.SubElement(track, 'creator').text = song['artist']
            ElementTree.SubElement(track, 'album').text = song['album']
            if song['tracknumber'] > 0:
                ElementTree.SubElement(track,
                                    'trackNum').text = str(song['tracknumber'])
            # XSPF files need the length in milliseconds as an integer.
            if song['length'] > 0:
                duration = str(int(round(song['length'] * 1000)))
                ElementTree.SubElement(track, 'duration').text = duration
            ElementTree.SubElement(track, 'image').text = cover_uri
            ElementTree.SubElement(track, 'location').text = song_uri
        # Make an ElementTree object out of our root <playlist> element and
        # write it to our file object.
        tree = ElementTree.ElementTree(root)
        tree.write(playlist, 'utf-8')
    else:
        raise cherrypy.HTTPError(501,'Not Implemented') 
    return playlist.getvalue(), ct
