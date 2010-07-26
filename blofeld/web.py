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
import anyjson
import thread
import hashlib
from random import shuffle

import cherrypy
from cherrypy.lib.static import serve_file

from Cheetah.Template import Template

from blofeld.config import *
from blofeld.transcode import transcode
import blofeld.utils as utils
import blofeld.utils.browsercap as browsercap
from blofeld.library import Library
from blofeld.coverart import find_cover, resize_cover
from blofeld.playlist import json_to_playlist
from blofeld.log import logger, enable_console, enable_file
from blofeld.download import create_archive


class WebInterface:
    """Handles any web requests, including API calls."""
    def __init__(self):
        # Create a library object to run queries against
        self.library = Library()
        # Do a startup scan for new music
        thread.start_new_thread(self.library.update, ())

    @cherrypy.expose
    def index(self):
        logger.debug("%s (%s)\tindex()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        template = Template(file=os.path.join(cfg['THEME_DIR'], 'index.tmpl'))
        return template.respond()

    @cherrypy.expose
    def list_albums(self, artists=None, query=None, output='json'):
        logger.debug("%s (%s)\tlist_albums(artists=%s, query=%s, output=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, artists, query, output, cherrypy.request.headers))
        if artists:
            artists = artists.split(',')
        albums = self.library.albums(artists, query)
        if output == 'json':
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return anyjson.serialize({'albums': albums})
        elif output == 'html':
            template = Template(file=os.path.join(cfg['THEME_DIR'], 'list_albums.tmpl'))
            template.albums = albums
            return template.respond()
        else:
            raise cherrypy.HTTPError(501,'Not Implemented') 

    @cherrypy.expose
    def list_artists(self, query=None, output='json'):
        logger.debug("%s (%s)\tlist_artists(query=%s, output=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, query, output, cherrypy.request.headers))
        artists = self.library.artists(query)
        if output == 'json':
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return anyjson.serialize({'artists': artists})
        elif output == 'html':
            template = Template(file=os.path.join(cfg['THEME_DIR'], 'list_artists.tmpl'))
            template.artists = artists
            return template.respond()
        else:
            raise cherrypy.HTTPError(501,'Not Implemented') 

    @cherrypy.expose
    def list_songs(self, artists=None ,albums=None, start=None, length=None,
                   query=None, list_all=False, archive=False, output='json'):
        logger.debug("%s (%s)\tlist_songs(artists=%s, albums=%s, start=%s, length=%s, query=%s, list_all=%s, archive=%s, output=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, artists, albums, start, length, query, list_all, archive, output, cherrypy.request.headers))
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
            return anyjson.serialize({'songs': songs})
        elif output == 'html':
            template = Template(file=os.path.join(cfg['THEME_DIR'], 'list_songs.tmpl'))
            template.songs = songs
            return template.respond()
        else:
            raise cherrypy.HTTPError(501,'Not Implemented') 

    @cherrypy.expose
    def get_playlist(self, artists=None, albums=None, query=None, format=None,
                     list_all=False, bitrate=None, output='xspf'):
        logger.debug("%s (%s)\tget_playlist(artists=%s, albums=%s, query=%s, format=%s, list_all=%s, bitrate=%s, output=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, artists, albums, query, format, list_all, bitrate, output, cherrypy.request.headers))
        if not (list_all or artists or albums or query):
            songs = []
        else:
            if artists:
                artists = artists.split(',')
            if albums:
                albums = albums.split(',')
            songs = self.library.songs(artists, albums, query)
        playlist, ct = json_to_playlist(cherrypy.request.base, songs, output,
                                                                format, bitrate)
        cherrypy.response.headers['Content-Type'] = ct
        return playlist

    @cherrypy.expose
    def get_song(self, songid=None, format=False, bitrate=False):
        logger.debug("%s (%s)\tget_song(songid=%s, format=%s, bitrate=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, songid, format, bitrate, cherrypy.request.headers))
        log_message = "%s (%s) requested " % (cherrypy.request.login, utils.find_originating_host(cherrypy.request.headers))
        try:
            range_request = cherrypy.request.headers['Range']
        except:
            range_request = "bytes=0-"
        try:
            song = self.library.db[songid]
            path = song['location'].encode(cfg['ENCODING'])
        except:
            log_message += "a song ID which could not be found: %s" % str(songid)
            logger.error(log_message)
            raise cherrypy.HTTPError(404)
        log_message += "%(title)s by %(artist)s from %(album)s " % song
        try:
            b = False
            #b = self.bc(cherrypy.request.headers['User-Agent'])
            if b:
                browser = "%s %s.%s on %s" % (b.name(), b.version()[0], b.version()[1], b.get("platform"))
            else:
                browser = cherrypy.request.headers['User-Agent']
            log_message += "using %s." % browser
        except:
            pass
        try:
            force_transcode = False
            if bitrate and \
               (int(bitrate) in [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112,
                                          128, 160, 192, 224, 256, 320]) and \
               (song['bitrate'] / 1024 > int(bitrate)):
                force_transcode = True
        except:
            pass
        uri = "file://" + urllib.pathname2url(path)
        song_file = urllib2.urlopen(uri)
        try:
            song_format = [song['mimetype'].split('/')[1],
                            os.path.splitext(path)[1].lower()[1:]]
        except:
            song_format = [os.path.splitext(path)[1].lower()[1:]]
        if not (format or bitrate):
            log_message += " The client did not request any specific format or bitrate so the file is being sent as-is (%s kbps %s)." % (str(song['bitrate'] / 1000), str(song_format))
            logger.info(log_message)
            return serve_file(path, song_file.info()['Content-Type'],
                                "inline", os.path.split(path)[1])
        if format:
            format = format.split(',')
        else:
            format = song_format
        logger.debug("The client wants %s and the file is %s" % (format, song_format))
        if True in [True for x in format if x in song_format] and not force_transcode:
            if bitrate:
                log_message += " The client requested %s kbps %s, but the file is already %s kbps %s, so the file is being sent as-is." % (bitrate, format, str(song['bitrate'] / 1000), str(song_format))
            else:
                log_message += " The client requested %s, but the file is already %s, so the file is being sent as-is." % (format, str(song_format))
            logger.info(log_message)
            return serve_file(path, song_file.info()['Content-Type'],
                                "inline", os.path.split(path)[1])
        else:
            if bitrate:
                log_message += " The client requested %s kbps %s, but the file is %s kbps %s, so we're transcoding the file for them." % (bitrate, format, str(song['bitrate'] / 1000), str(song_format))
            else:
                log_message += " The client requested %s, but the file %s, so we're transcoding the file for them." % (format, str(song_format))
            logger.info(log_message)
        # If we're transcoding audio and the client is trying to make range
        # requests, we have to throw an error 416. This sucks because it breaks
        # <audio> in all the WebKit browsers I've tried, but at least it stops
        # them from spawning a zillion transcoder threads (I'm looking at you,
        # Chromium).
        if True in [True for x in format if x in ['mp3']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                logger.debug("Got a range request for a file that needs transcoded: %s" % range_request)
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/mpeg'
                #cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
                return transcode(path, 'mp3', bitrate)
        elif True in [True for x in format if x in ['ogg', 'vorbis', 'oga']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                logger.debug("Got a range request for a file that needs transcoded: %s" % range_request)
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/ogg'
                #cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
                return transcode(path, 'ogg', bitrate)
        elif True in [True for x in format if x in ['m4a', 'aac', 'mp4']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                logger.debug("Got a range request for a file that needs transcoded: %s" % range_request)
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/x-m4a'
                #cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
                return transcode(path, 'm4a', bitrate)
        else:
            raise cherrypy.HTTPError(501) 
    get_song._cp_config = {'response.stream': True}

    @cherrypy.expose
    def get_cover(self, songid=None, size='original', download=False):
        logger.debug("%s (%s)\tget_cover(songid=%s, size=%s, download=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, songid, size, download, cherrypy.request.headers))
        try:
            song = self.library.db[songid]
        except:
            raise cherrypy.HTTPError(404) 
        try:
            size = int(size)
        except:
            size = 'original'
        cover = find_cover(song)
        if cover is None:
            raise cherrypy.HTTPError(404,'Not Found') 
        uri = 'file://' + urllib.pathname2url(cover.encode(cfg['ENCODING']))
        if size != 'original':
            artwork = resize_cover(song, cover, uri, size)
        else:
            artwork = urllib2.urlopen(uri)
        if download:
            return serve_file(cover,
                        artwork.info()['Content-Type'], "attachment", os.path.basename(cover))
        cherrypy.response.headers['Content-Type'] = artwork.info()['Content-Type']
        return artwork.read()

    @cherrypy.expose
    def download(self, songs=None, artists=None ,albums=None, query=None):
        logger.debug("%s (%s)\tdownload(songs=%s, artists=%s, albums=%s, query=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, songs, artists, albums, query, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['download']:
            logger.warn("%(user)s (%(ip)s) requested a download, but was denied because %(user)s is not a member of the download group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        file_list = []
        if not songs and not artists and not albums and not query:
            raise cherrypy.HTTPError(501) 
        elif songs:
            songs = songs.split(',')
            if len(songs) > 100:
                return "Too many songs! Please narrow your criteria."
            for song in songs:
                try:
                    file_list.append(self.library.db[song])
                except:
                    raise cherrypy.HTTPError(404,'Not Found')
        else:
            if artists:
                artists = artists.split(',')
            if albums:
                albums = albums.split(',')
            files = self.library.songs(artists, albums, query)
            if len(files) > 100:
                return "Too many songs! Please narrow your criteria."
            for song in files:
                file_list.append(self.library.db[song['id']])
        archive = create_archive(file_list)
        try:
            return serve_file(archive, 'application/zip', 'download.zip')
        except:
            logger.debug("Something went wrong while sending the archive.")
        finally:
            logger.debug("Removing archive.")
            os.remove(archive)

    @cherrypy.expose
    def update_library(self):
        logger.debug("%s (%s)\tupdate()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['admin']:
            logger.warn("%(user)s (%(ip)s) requested a library update, but was denied because %(user)s is not a member of the admin group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        def update():
            yield "Updating library...\n"
            thread.start_new_thread(self.library.update, ())
            while not self.library.updating.acquire(False):
                yield ".\n"
                sleep(1)
            self.library.updating.release()
            yield "Done.\n"
        return update()
    update_library._cp_config = {'response.stream': True}

    @cherrypy.expose
    def random(self, songs=None, artists=None ,albums=None, query=None, limit=None):
        logger.debug("%s (%s)\trandom(songs=%s, artists=%s, albums=%s, query=%s, limit=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, songs, artists, albums, query, limit,  cherrypy.request.headers))
        song_list = []
        if artists:
            artists = artists.split(',')
        if albums:
            albums = albums.split(',')
        files = self.library.songs(artists, albums, query)
        if songs:
            songs = songs.split(',')
            for song in files:
                if song['id'] in songs:
                    songs_list.append(song)
        else:
            song_list = files
        shuffle(song_list)
        try:
            limit = int(limit)
        except:
            limit = len(song_list)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return anyjson.serialize(song_list[:limit])

    @cherrypy.expose
    def suggest(self, term=None):
        logger.debug("%s (%s)\tsuggest(term=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, term, cherrypy.request.headers))
        result = self.library.songs(suggest=True, query=term)
        return anyjson.serialize(result[:5])

    @cherrypy.expose
    def shutdown(self):
        logger.debug("%s (%s)\tshutdown()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['admin']:
            logger.warn("%(user)s (%(ip)s) requested that the server shut down, but was denied because %(user)s is not a member of the admin group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        def quit():
            logger.info("Received shutdown request, complying.")
            yield "Blofeld is shutting down.\n"
            cherrypy.engine.exit()
        return quit()
    shutdown._cp_config = {'response.stream': True}


def start(log_level='warn'):
    """Starts the CherryPy web server and initiates the logging module."""
    
    def cleartext(password):
        return password
    
    cherrypy.config.update({
        'server.socket_host': cfg['HOSTNAME'],
        'server.socket_port': cfg['PORT'],
        'tools.encode.on': True, 
        'tools.encode.encoding': 'utf-8',
        'tools.gzip.on': True,
        'log.screen': cfg['CHERRYPY_OUTPUT'],
        'tools.basic_auth.on': cfg['REQUIRE_LOGIN'],
        'tools.basic_auth.realm': 'Blofeld',
        'tools.basic_auth.users': cfg['USERS'],
        'tools.basic_auth.encrypt': cleartext
        })

    static = {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(cfg['THEME_DIR'], 'static')
            }

    conf = {
        '/static': static,
        '/blofeld/static': static
        }

    application = cherrypy.tree.mount(WebInterface(), '/', config=conf)

    logger.debug("Starting CherryPy server.")
    cherrypy.engine.start()
    cherrypy.engine.block()
