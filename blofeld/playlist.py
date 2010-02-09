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


def json_to_playlist(base_url, songs, output='xspf', format=None):
    playlist = StringIO.StringIO()
    if not format:
        format = ''
    else:
        format = '&format=' + format
    if output == 'm3u':
        ct = 'audio/x-mpegurl'
        playlist.write('#EXTM3U\n')
        for song in songs:
            info = str(int(round(song['length']))) + "," + song['artist'] + " - " + song['title']
            uri = base_url + '/get_song?songid=' + song['id'] + format
            playlist.write('\n#EXTINF:' + info + '\n')
            playlist.write(uri + "\n")
    elif output == 'pls':
        ct = 'audio/x-scpls'
        counter = 1
        playlist.write('[playlist]\n')
        playlist.write('\nNumberOfEntries=' + str(len(songs)) + '\n')
        for song in songs:
            uri = base_url + '/get_song?songid=' + song['id'] + format
            playlist.write('\nFile' + str(counter) + '=' + uri)
            playlist.write('\nTitle' + str(counter) + '=' + song['artist'] + " - " + song['title'])
            if int(round(song['length'])) == 0:
                length = '-1'
            else:
                length = str(int(round(song['length'])))
            playlist.write('\nLength' + str(counter) + '=' + length + '\n')
            counter += 1
        playlist.write('\nVersion=2\n')
    elif output == 'xspf':
        ct = 'application/xspf+xml'
        root = ElementTree.Element('playlist', version='1', xmlns='http://xspf.org/ns/0/')
        tracklist = ElementTree.SubElement(root, 'tracklist')
        for song in songs:
            song_uri = base_url + '/get_song?songid=' + song['id'] + format
            cover_uri = base_url + '/get_cover?size=500&songid=' + song['id']
            track = ElementTree.SubElement(tracklist, 'track')
            ElementTree.SubElement(track, 'title').text = song['title']
            ElementTree.SubElement(track, 'creator').text = song['artist']
            ElementTree.SubElement(track, 'album').text = song['album']
            if song['tracknumber'] > 0:
                ElementTree.SubElement(track, 'trackNum').text = str(song['tracknumber'])
            if song['length'] > 0:
                duration = str(int(round(song['length'] * 1000)))
                ElementTree.SubElement(track, 'duration').text = duration
            ElementTree.SubElement(track, 'image').text = cover_uri
            ElementTree.SubElement(track, 'location').text = song_uri
        tree = ElementTree.ElementTree(root)
        tree.write(playlist, 'utf-8')
    else:
        raise cherrypy.HTTPError(501,'Not Implemented') 
    return playlist.getvalue(), ct
