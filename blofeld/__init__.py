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
from blofeld.library import Library
from blofeld.coverart import resize_cover

library = Library()

class Blofeld:
    def __init__(self):
        pass

    @cherrypy.expose
    def index(self):
        template = Template(file=os.path.join(THEME_DIR, 'index.tmpl'))
#        template.songs = l_songs
        return template.respond()

    @cherrypy.expose
    def list_albums(self, artists=None, query=None, output='json'):
        l_albums = library.albums()
        l_songs = library.songs()
        l_artists = library.artists()
        l_relationships = library.relationships()
        result = None
        if artists:
            result = {}
            artists = artists.split(',')
            for artist in artists:
                for album in l_relationships[artist]:
                    result[album] = l_albums[album]
        if query:
            query = util.clean_text(query)
            filter_result = {}
            if not result:
                result = l_albums
            for song in l_songs:
                for field in ('artist', 'album', 'title'):
                    if query in util.clean_text(l_songs[song][field]) and \
                       l_songs[song]['album_hash'] in result and \
                       l_songs[song]['album_hash'] not in filter_result:
                        filter_result[l_songs[song]['album_hash']] = l_songs[song]['album']
            result = filter_result
        if output == 'json':
            if result != None:
                return str(result)
            else:
                return str(l_albums)
        template = Template(file=os.path.join(THEME_DIR, 'list_albums.tmpl'))
        if result != None:
            template.albums = result
        else: 
            template.albums = l_albums
        return template.respond()

    @cherrypy.expose
    def list_artists(self, query=None,  output='json'):
        l_songs = library.songs()
        l_artists = library.artists()
        result = None
        if query:
            query = util.clean_text(query)
            result = {}
            for song in l_songs:
                for field in ('artist', 'album', 'title'):
                    if query in util.clean_text(l_songs[song][field]) and \
                       l_songs[song]['artist_hash'] not in result:
                        result[l_songs[song]['artist_hash']] = l_songs[song]['artist']
        if output == 'json':
            if result != None:
                return str(result)
            else:
                return str(l_artists)
        template = Template(file=os.path.join(THEME_DIR, 'list_artists.tmpl'))
        if result != None:
            template.artists = result
        else:
            template.artists = l_artists
        return template.respond()

    @cherrypy.expose
    def list_songs(self, artists=None,
                   albums=None, query=None, list_all=False, output='json'):
        l_albums = library.albums()
        l_songs = library.songs()
        l_artists = library.artists()
        l_relationships = library.relationships()
        if list_all:
            return str(l_songs)
        result = None
        if albums and not artists:
            result = {}
            albums = albums.split(',')
            for album in albums:
                for artist in l_relationships:
                    if album in l_relationships[artist]:
                        for song in l_relationships[artist][album]:
                            result[song] = l_songs[song]
        if artists and not albums:
            result = {}
            artists = artists.split(',')
            for artist in artists:
                for album in l_relationships[artist]:
                    for song in l_relationships[artist][album]:
                        result[song] = l_songs[song]
        if (artists != None) and (albums != None):
            result = {}
            artists = artists.split(',')
            albums = albums.split(',')
            for album in albums:
                for artist in artists:
                    try:
                        for song in l_relationships[artist][album]:
                            result[song] = l_songs[song]
                    except:
                        pass
        if query:
            query = util.clean_text(query)
            filter_result = {}
            if not result:
                result = l_songs
            for song in result:
                for field in ('artist', 'album', 'title'):
                    if query in util.clean_text(result[song][field]) and \
                       song not in filter_result:
                        filter_result[song] = result[song]
            result = filter_result
        if output =='json':
            if result == None:
                result = {}
            return str(result)
        template = Template(file=os.path.join(THEME_DIR, 'list_songs.tmpl'))
        if result == None:
            result = {}
        template.songs = result
        return template.respond()

    @cherrypy.expose
    def get_song(self, songid=None, download=False, format=None):
        l_songs = library.songs()
        if songid not in l_songs:
            return "False"
        uri = l_songs[songid]['location']
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
        song = library.db[songid]
        uri = song['location']
        path = os.path.split(urllib.url2pathname(urlparse(uri).path))[0]
        cover = 'Cover.jpg'
        if download:
            return serve_file(os.path.join(path, cover),
                           artwork.info()['Content-Type'], "attachment", cover)
        if size != 'original':
            artwork = resize_cover(songid, uri, size)
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
