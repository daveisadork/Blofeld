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
import sys
import urllib
import urllib2
import cjson as json

import cherrypy
from cherrypy.lib.static import serve_file

from Cheetah.Template import Template

from blofeld.config import *
import blofeld.transcode as transcode
import blofeld.util as util
from blofeld.library import Library
from blofeld.coverart import resize_cover
from blofeld.playlist import json_to_playlist

class WebInterface:
    def __init__(self):
        self.library = Library()

    @cherrypy.expose
    def index(self):
        template = Template(file=os.path.join(THEME_DIR, 'index.tmpl'))
        return template.respond()

    @cherrypy.expose
    def list_albums(self, artists=None, query=None, output='json'):
        albums = self.library.albums(artists, query)
        if output == 'json':
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.encode(albums)
        elif output == 'html':
            template = Template(file=os.path.join(THEME_DIR, 'list_albums.tmpl'))
            template.albums = albums
            return template.respond()
        else:
            raise cherrypy.HTTPError(501,'Not Implemented') 

    @cherrypy.expose
    def list_artists(self, query=None, output='json'):
        artists = self.library.artists(query)
        if output == 'json':
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.encode(artists)
        elif output == 'html':
            template = Template(file=os.path.join(THEME_DIR, 'list_artists.tmpl'))
            template.artists = artists
            return template.respond()
        else:
            raise cherrypy.HTTPError(501,'Not Implemented') 

    @cherrypy.expose
    def list_songs(self, artists=None ,albums=None, start=None, length=None,
                   query=None, list_all=False, archive=False, output='json'):
        if not list_all and not artists and not albums and not query and not archive:
            songs = []
        else:
            songs = self.library.songs(artists, albums, query)
        if start and length:
            start = int(start)
            end = int(length) + start
            if len(songs) - 1 < end:
                end = -1
            songs = songs[start:end]
        if output == 'json':
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.encode(songs)
        elif output == 'html':
            template = Template(file=os.path.join(THEME_DIR, 'list_songs.tmpl'))
            template.songs = songs
            return template.respond()
        else:
            raise cherrypy.HTTPError(501,'Not Implemented') 

    @cherrypy.expose
    def get_playlist(self, artists=None ,albums=None, query=None, format=None,
                     list_all=False, output='xspf'):
        if not list_all and not artists and not albums and not query:
            songs = []
        else:
            songs = self.library.songs(artists, albums, query)
        playlist, ct = json_to_playlist(cherrypy.request.base, songs, output, format)
        cherrypy.response.headers['Content-Type'] = ct
        return playlist
#        else:
#            return "Not implemented."

    @cherrypy.expose
    def get_song(self, songid=None, download=False, format=None):
        song = self.library.db[songid]
        try: path = song['location'].encode(ENCODING)
        except: raise cherrypy.HTTPError(404,'Not Found') 
        try: song_format = song['mimetype'].split('/')[1]
        except: song_format = os.path.splitext(path)[1].lower()[1:]
        uri = "file://" + urllib.pathname2url(path)
        song_file = urllib2.urlopen(uri)
        if format == 'mp3': return transcode.to_mp3(path)
        elif format == 'ogg': return transcode.to_ogg(path)
        elif not format:
            return serve_file(path, song_file.info()['Content-Type'],
                              "inline", os.path.split(path)[1])
        else: raise cherrypy.HTTPError(501,'Not Implemented') 
    get_song._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_cover(self, songid=None, size='original', download=False):
        song = self.library.db[songid]
        try: size = int(size)
        except: size = 'original'
        try: path = os.path.split(song['location'])[0].encode(ENCODING)
        except: raise cherrypy.HTTPError(404,'Not Found') 
        filename = 'Cover.jpg'
        uri = "file://" + urllib.pathname2url(os.path.join(path, filename))
        if size != 'original': artwork = resize_cover(songid, path, uri, size)
        else: artwork = urllib2.urlopen(uri)
        if download:
            return serve_file(os.path.join(path, filename),
                           artwork.info()['Content-Type'], "attachment", filename)
        cherrypy.response.headers['Content-Type'] = artwork.info()['Content-Type']
        return artwork.read()

    @cherrypy.expose
    def shutdown(self):
        def quit():
            yield "Blofeld is shutting down."
            sys.exit()
        return quit()
    shutdown._cp_config = {'response.stream': True}

def start():
    cherrypy.config.update({
        'server.socket_host': HOSTNAME,
        'server.socket_port': PORT,
        'tools.encode.on': True, 
        'tools.encode.encoding': 'utf-8',
        'tools.gzip.on': True
        })

    static = {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(THEME_DIR, 'static')
        }

    conf = {
        '/static': static,
        '/blofeld/static': static
        }

    cherrypy.quickstart(WebInterface(), '/', config=conf)
