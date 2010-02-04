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


import cherrypy
from cherrypy.lib.static import serve_file

from Cheetah.Template import Template

from blofeld.config import *
from blofeld.transcode import transcode
import blofeld.util as util
from blofeld.library import Library
from blofeld.coverart import resize_cover

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
            return str(albums)
        elif output == 'html':
            template = Template(file=os.path.join(THEME_DIR, 'list_albums.tmpl'))
            template.albums = albums
            return template.respond()
        else:
            return "Not implemented."


    @cherrypy.expose
    def list_artists(self, query=None, output='json'):
        artists = self.library.artists(query)
        if output == 'json':
            return str(artists)
        elif output == 'html':
            template = Template(file=os.path.join(THEME_DIR, 'list_artists.tmpl'))
            template.artists = artists
            return template.respond()
        else:
            return "Not implemented."

    @cherrypy.expose
    def list_songs(self, artists=None,
                   albums=None, query=None, list_all=False, output='json'):
        if not list_all and not artists and not albums and not query:
            songs = {}
        else:
            songs = self.library.songs(artists, albums, query)
        if output == 'json':
            return str(songs)
        elif output == 'html':
            template = Template(file=os.path.join(THEME_DIR, 'list_songs.tmpl'))
            template.songs = songs
            return template.respond()
        else:
            return "Not implemented."

    @cherrypy.expose
    def get_song(self, songid=None, download=False, format=None):
        song = self.library.db[songid]
        try:
            path = song['location']
        except:
            return "Not found."
        uri = "file://" + urllib.pathname2url(path.encode(ENCODING))
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
        song = self.library.db[songid]
        try:
            size = int(size)
        except:
            size = 'original'
        try:
            path = os.path.split(song['location'])[0]
        except:
            return "Not found."
        filename = 'Cover.jpg'
        uri = "file://" + urllib.pathname2url(
               os.path.join(path, filename).encode(ENCODING))
        if download:
            return serve_file(os.path.join(path, filename),
                           artwork.info()['Content-Type'], "attachment", filename)
        if size != 'original':
            artwork = resize_cover(songid, path, uri, size)
        else:
            artwork = urllib2.urlopen(uri)
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
        'tools.encode.encoding': 'utf-8'
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
