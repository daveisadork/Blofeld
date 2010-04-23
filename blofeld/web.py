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
from blofeld.transcode import transcode
import blofeld.util as util
from blofeld.library import Library
from blofeld.coverart import find_cover, resize_cover
from blofeld.playlist import json_to_playlist
from blofeld.log import log

class WebInterface:
    """Handles any web requests, including API calls."""
    def __init__(self):
        # Create a library object to run queries against
        self.library = Library()

    @cherrypy.expose
    def index(self):
        template = Template(file=os.path.join(THEME_DIR, 'index.tmpl'))
        return template.respond()

    @cherrypy.expose
    def list_albums(self, artists=None, query=None, output='json'):
        if artists:
            artists = artists.split(',')
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
            if artists:
                artists = artists.split(',')
            if albums:
                albums = albums.split(',')
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
    def get_playlist(self, artists=None, albums=None, query=None, format=None,
                     list_all=False, bitrate=None, output='xspf'):
        if not (list_all or artists or albums or query):
            songs = []
        else:
            if artists:
                artists = artists.split(',')
            if albums:
                albums = albums.split(',')
            songs = self.library.songs(artists, albums, query)
        print cherrypy.request.base
        playlist, ct = json_to_playlist(cherrypy.request.base, songs, output, format, bitrate)
        cherrypy.response.headers['Content-Type'] = ct
        return playlist

    @cherrypy.expose
    def get_song(self, songid=None, download=False, format=None, bitrate=False):
        print "\n\n\n", cherrypy.request.headers, "\n\n\n"
        try:
            range_request = cherrypy.request.headers['Range']
        except:
            range_request = "bytes=0-"
        try:
            song = self.library.db[songid]
            path = song['location'].encode(ENCODING)
        except:
            raise cherrypy.HTTPError(404)
        try:
            force_transcode = False
            if format and bitrate and \
               (int(bitrate) in [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]) and \
               (song['bitrate'] / 1024 > int(bitrate)):
                force_transcode = True
        except:
            pass
        uri = "file://" + urllib.pathname2url(path)
        song_file = urllib2.urlopen(uri)
        try:
            log("%(ip)s played %(title)s by %(artist)s from %(album)s." % \
                {
                    'ip': cherrypy.request.headers['X-Real-Ip'],
                    'artist': song['artist'],
                    'album': song['album'],
                    'title': song['title']
                }
            )
        except:
            pass
        if not format:
            return serve_file(path, song_file.info()['Content-Type'],
                                "inline", os.path.split(path)[1])
        format = format.split(',')
        try:
            song_format = [song['mimetype'].split('/')[1],
                            os.path.splitext(path)[1].lower()[1:]]
        except:
            song_format = [os.path.splitext(path)[1].lower()[1:]]
        print "Client wants", format, "and the file is", song_format
        if True in [True for x in format if x in song_format] and not force_transcode:
            return serve_file(path, song_file.info()['Content-Type'],
                                "inline", os.path.split(path)[1])
        # If we're transcoding audio and the client is trying to make range
        # requests, we have to throw an error 416. This sucks because it breaks
        # <audio> in all the WebKit browsers I've tried, but at least it stops
        # them from spawning a zillion transcoder threads (I'm looking at you,
        # Chromium).
        elif True in [True for x in format if x in ['mp3']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/mpeg'
                return transcode(path, 'mp3', bitrate)
        elif True in [True for x in format if x in ['ogg', 'vorbis', 'oga']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/ogg'
                return transcode(path, 'ogg', bitrate)
        else:
            raise cherrypy.HTTPError(501) 
    get_song._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_cover(self, songid=None, size='original', download=False):
        try:
            song = self.library.db[songid]
        except:
            raise cherrypy.HTTPError(404) 
        try:
            size = int(size)
        except:
            size = 'original'
        cover = find_cover(song['location'].encode(ENCODING), songid)
        if cover is None:
            raise cherrypy.HTTPError(404,'Not Found') 
        uri = 'file://' + urllib.pathname2url(cover)
        if size != 'original':
            artwork = resize_cover(songid, cover, uri, size)
        else:
            artwork = urllib2.urlopen(uri)
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


def setup():
    """Starts the CherryPy web server, or configures it to run behind Apache
    or some other web server.
    """

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

    if USE_INTERNAL:
        cherrypy.config.update({'log.screen': True})
    else:
        cherrypy.engine.SIGHUP = None
        cherrypy.engine.SIGTERM = None
        cherrypy.server.unsubscribe()

    cherrypy.tree.mount(WebInterface(), "/", config=conf)

def start():
    setup()
    cherrypy.engine.start()
