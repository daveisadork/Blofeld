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

import os
import sys
import urllib
import urllib2
from urlparse import urlparse

import cherrypy
from cherrypy.lib.static import serve_file

from Cheetah.Template import Template

from blofeld.config import *
from blofeld.transcode import transcode
import blofeld.util as util
import blofeld.library as library
from blofeld.coverart import resize_cover

class Blofeld:

    @cherrypy.expose
    def index(self):
        template = Template(file=os.path.join(THEME_DIR, 'index.tmpl'))
        template.songs = library.songs
        return template.respond()

    @cherrypy.expose
    def list_albums(self, artists=None, query=None, output='json'):
        result = None
        if artists:
            result = {}
            artists = artists.split(',')
            for artist in artists:
                for album in library.relationships[artist]:
                    result[album] = library.albums[album]
        if query:
            query = util.clean_text(query)
            filter_result = {}
            if not result:
                result = library.albums
            for song in library.songs:
                for field in ('artist', 'album', 'title'):
                    if query in util.clean_text(library.songs[song][field]) and \
                       library.songs[song]['album_hash'] in result and \
                       library.songs[song]['album_hash'] not in filter_result:
                        filter_result[library.songs[song]['album_hash']] = library.songs[song]['album']
            result = filter_result
        if output == 'json':
            if result != None:
                return str(result)
            else:
                return str(library.albums)
        template = Template(file=os.path.join(THEME_DIR, 'list_albums.tmpl'))
        if result != None:
            template.albums = result
        else: 
            template.albums = library.albums
        return template.respond()

    @cherrypy.expose
    def list_artists(self, query=None,  output='json'):
        result = None
        if query:
            query = util.clean_text(query)
            result = {}
            for song in library.songs:
                for field in ('artist', 'album', 'title'):
                    if query in util.clean_text(library.songs[song][field]) and \
                       library.songs[song]['artist_hash'] not in result:
                        result[library.songs[song]['artist_hash']] = library.songs[song]['artist']
        if output == 'json':
            if result != None:
                return str(result)
            else:
                return str(library.artists)
        template = Template(file=os.path.join(THEME_DIR, 'list_artists.tmpl'))
        if result != None:
            template.artists = result
        else:
            template.artists = library.artists
        return template.respond()

    @cherrypy.expose
    def list_songs(self, artists=None,
                   albums=None, query=None, list_all=False, output='json'):
        if list_all:
            return str(library.songs)
        result = None
        if albums and not artists:
            result = {}
            albums = albums.split(',')
            for album in albums:
                for artist in library.relationships:
                    if album in library.relationships[artist]:
                        for song in library.relationships[artist][album]:
                            result[song] = library.songs[song]
        if artists and not albums:
            result = {}
            artists = artists.split(',')
            for artist in artists:
                for album in library.relationships[artist]:
                    for song in library.relationships[artist][album]:
                        result[song] = library.songs[song]
        if (artists != None) and (albums != None):
            result = {}
            artists = artists.split(',')
            albums = albums.split(',')
            for album in albums:
                for artist in artists:
                    try:
                        for song in library.relationships[artist][album]:
                            result[song] = library.songs[song]
                    except:
                        pass
        if query:
            query = util.clean_text(query)
            filter_result = {}
            if not result:
                result = library.songs
            for song in result:
                for field in ('artist', 'album', 'title'):
                    if query in util.clean_text(result[song][field]) and \
                       song not in filter_result:
                        filter_result[song] = result[song]
            result = filter_result
        if output =='json':
            if result == None:
                result = {}
            return result
        template = Template(file=os.path.join(THEME_DIR, 'list_songs.tmpl'))
        if result == None:
            result = {}
        template.songs = result
        return template.respond()

    @cherrypy.expose
    def get_song(self, songid=None, download=False, format=None):
        if songid not in library.songs:
            return "False"
        uri = library.songs[songid]['location']
        path = urllib.url2pathname(urlparse(uri).path)
        song = urllib2.urlopen(uri)
        if download and not format:
            return serve_download(path, os.path.split(path)[1])
        if format != None:
            return transcode(path, song, format)
        else:
            return serve_file(path, song.info()['Content-Type'],
                              "inline", os.path.split(path)[1])
        return False
    get_song._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_cover(self, songid=None, size='original', download=False):
        uri = library.songs[songid]['location']
        path = os.path.split(urllib.url2pathname(urlparse(uri).path))[0]
        cover = 'Cover.jpg'
        if download:
            return serve_file(os.path.join(path, cover),
                           artwork.info()['Content-Type'], "attachment", cover)
        if size != 'original':
            artwork = resize_cover(songid, size)
        else:
            artwork = urllib2.urlopen('file://' + 
                                urllib.pathname2url(os.path.join(path, cover)))
        cherrypy.response.headers['Content-Type'] = artwork.info()['Content-Type']
        return artwork.read()

    @cherrypy.expose
    def shutdown(self):
        def quit():
            yield "Blofeld is shutting down."
            sys.exit()
        return quit()
    shutdown._cp_config = {'response.stream': True}
