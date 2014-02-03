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
import json
import anyjson
import thread
import hashlib
import mimetypes
mimetypes.init()
import shlex
import fnmatch
import types
import time
from operator import itemgetter
from random import shuffle
from threading import Event

import cherrypy
from cherrypy.lib.static import serve_file

from Cheetah.Template import Template

from blofeld.config import *
from blofeld.transcode import Transcoder
import blofeld.utils as utils
from blofeld.library import Library
from blofeld.coverart import find_cover, resize_cover
from blofeld.playlist import json_to_playlist
from blofeld.log import logger
from blofeld.download import create_archive

library = Library()
transcoder = Transcoder()
shutting_down = Event()

class WebInterface:
    """Handles any web requests, including API calls."""
    def __init__(self):
        # Create a library object to run queries against
        self.library = library
        self.transcoder = transcoder

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
        songs.sort(key=itemgetter('albumartist', 'album', 'date', 'discnumber', 'tracknumber'))
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
    def get_tags(self, songid=None):
        logger.debug("%s (%s)\tget_tags(songid=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, songid, cherrypy.request.headers))
        if not songid:
            raise cherrypy.HTTPError(501, "You must supply a song id.")
        if self.library.db.doc_exist(songid):
            song = self.library.db[songid]
            if song['type'] != 'song':
                raise cherrypy.HTTPError(501, "The specified document is not a song.")
            song['id'] = song['_id']
            del song['_id']
            del song['location']
            del song['_rev']
            del song['type']
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return anyjson.serialize({"song": song})
        else:
            raise cherrypy.HTTPError(404, "That song doesn't exist in the database.")


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
            path = song['location']
        except:
            log_message += "a song ID which could not be found: %s" % str(songid)
            logger.error(log_message)
            raise cherrypy.HTTPError(404)
        log_message += "%s by %s from %s " % (song['title'].encode(cfg['ENCODING']), song['artist'].encode(cfg['ENCODING']), song['album'].encode(cfg['ENCODING']))
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
            if bitrate:
                bitrate = str(bitrate)
            force_transcode = False
            if bitrate and \
               (int(bitrate) in [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112,
                                          128, 160, 192, 224, 256, 320]) and \
               (song['bitrate'] / 1024 > int(bitrate)):
                force_transcode = True
        except:
            pass
        try:
            song_format = [song['mimetype'].split('/')[1],
                            os.path.splitext(path)[1].lower()[1:]]
        except:
            song_format = [os.path.splitext(path)[1].lower()[1:]]
        if True in [True for x in song_format if x in ['mp3']]:
            song_mime = 'audio/mpeg'
            song_format = ['mp3']
        elif True in [True for x in song_format if x in ['ogg', 'vorbis', 'oga']]:
            song_mime = 'audio/ogg'
            song_format = ['ogg', 'vorbis', 'oga']
        elif True in [True for x in song_format if x in ['m4a', 'aac', 'mp4']]:
            song_mime = 'audio/x-m4a'
            song_format = ['m4a', 'aac', 'mp4']
        else:
            song_mime = 'application/octet-stream'
        if not (format or bitrate):
            log_message += " The client did not request any specific format or bitrate so the file is being sent as-is (%s kbps %s)." % (str(song['bitrate'] / 1000), str(song_format))
            logger.info(log_message)
            if not os.name == 'nt':
                path = path.encode(cfg['ENCODING'])
            return serve_file(path, song_mime,
                                "inline", os.path.split(path)[1])
        if format:
            format = str(format).split(',')
        else:
            format = song_format
        logger.debug("The client wants %s and the file is %s" % (format, song_format))
        if True in [True for x in format if x in song_format] and not force_transcode:
            if bitrate:
                log_message += " The client requested %s kbps %s, but the file is already %s kbps %s, so the file is being sent as-is." % (bitrate, format, str(song['bitrate'] / 1000), str(song_format))
            else:
                log_message += " The client requested %s, but the file is already %s, so the file is being sent as-is." % (format, str(song_format))
            logger.info(log_message)
            if not os.name == 'nt':
                path = path.encode(cfg['ENCODING'])
            return serve_file(path, song_mime,
                                "inline", os.path.split(path)[1])
        else:
            if bitrate:
                log_message = " The client requested %s kbps %s, but the file is %s kbps %s, so we're transcoding the file for them." % (bitrate, format, str(song['bitrate'] / 1000), str(song_format))
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
                try:
                    if cherrypy.request.headers['Referer'].lower().endswith('jplayer.swf'):
                        cherrypy.response.headers['Content-Type'] = 'audio/mp3'
                except:
                    pass
                #cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
                return self.transcoder.transcode(path, 'mp3', bitrate)
        elif True in [True for x in format if x in ['ogg', 'vorbis', 'oga']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                logger.debug("Got a range request for a file that needs transcoded: %s" % range_request)
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/ogg'
                #cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
                return self.transcoder.transcode(path, 'ogg', bitrate)
        elif True in [True for x in format if x in ['m4a', 'aac', 'mp4']]:
#            cherrypy.response.headers['Content-Length'] = '-1'
            if range_request != 'bytes=0-':
                logger.debug("Got a range request for a file that needs transcoded: %s" % range_request)
                raise cherrypy.HTTPError(416)
            else:
                cherrypy.response.headers['Content-Type'] = 'audio/x-m4a'
                #cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
                return self.transcoder.transcode(path, 'm4a', bitrate)
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
        if download:
            return serve_file(cover,
                        mimetypes.guess_type(cover)[0], "attachment", os.path.basename(cover))
        if size != 'original':
            artwork = resize_cover(song, cover, size)
        else:
            artwork = cover
        cherrypy.response.headers['Content-Type'] = mimetypes.guess_type(cover)[0]
        return serve_file(artwork,
                        mimetypes.guess_type(artwork)[0], "inline", os.path.basename(artwork))

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
    download._cp_config = {'response.stream': True}

    @cherrypy.expose
    def update_library(self, ticket=None):
        #logger.debug("%s (%s)\tupdate()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['admin']:
            logger.warn("%(user)s (%(ip)s) requested a library update, but was denied because %(user)s is not a member of the admin group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if not ticket:
            return anyjson.serialize({"ticket": self.library.update()})
        else:
            return anyjson.serialize(self.library.update(ticket=ticket))

    scan = update_library
    scan.exposed = True

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
        return anyjson.serialize(result)

    @cherrypy.expose
    def config(self, set_option=None, get_option=None, value=None):
        logger.debug("%s (%s)\tconfig()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['admin']:
            logger.warn("%(user)s (%(ip)s) requested configuration data, but was denied because %(user)s is not a member of the admin group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        if set_option:
            if not value:
                raise cherrypy.HTTPError(501,'No value provided for the requested option')
            if set_option not in cfg.keys():
                raise cherrypy.HTTPError(501,'The requested option does not exist')
            try:
                if type(cfg[set_option]) is types.ListType:
                    value = value.split(',')
                if type(cfg[set_option]) is types.BooleanType:
                    value = anyjson.deserialize(value)
                if type(cfg[set_option]) is types.StringType:
                    value = str(value)
            except:
                raise cherrypy.HTTPError(501, 'The value provided was the wrong type. Expected a %s' % type(cfg[set_option]))
            try:
                cfg[set_option] = value
                cfg.save_config()
                cherrypy.response.headers['Content-Type'] = 'application/json'
                return anyjson.serialize({'config': {set_option: cfg[set_option]}})
            except Exception as x:
                logger.error("Could not save configuration. The error was: %s" % str(x))
        if get_option:
            if get_option not in cfg.keys():
                raise cherrypy.HTTPError(501,'The requested option does not exist')
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return anyjson.serialize({'config': {get_option: cfg[get_option]}})
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return anyjson.serialize({'config': cfg})

    @cherrypy.expose
    def shutdown(self):
        logger.debug("%s (%s)\tshutdown()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['admin']:
            logger.warn("%(user)s (%(ip)s) requested that the server shut down, but was denied because %(user)s is not a member of the admin group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        try:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logger.info("Received shutdown request, complying.")
            self.transcoder.stop()
            self.library.scanner.stop()
            return anyjson.serialize({'shutdown': True})
        except:
            pass
        finally:
            shutting_down.set()
            logger.debug("Stopping CherryPy.")
            cherrypy.engine.exit()

    @cherrypy.expose
    def flush_db(self):
        logger.debug("%s (%s)\tshutdown()\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, cherrypy.request.headers))
        if cfg['REQUIRE_LOGIN'] and cherrypy.request.login not in cfg['GROUPS']['admin']:
            logger.warn("%(user)s (%(ip)s) requested that the database be flushed, but was denied because %(user)s is not a member of the admin group." % {'user': cherrypy.request.login, 'ip': utils.find_originating_host(cherrypy.request.headers)})
            raise cherrypy.HTTPError(401,'Not Authorized')
        try:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            logger.info("Received flush database request, complying.")
            return anyjson.serialize({'flush_db': True})
        except:
            pass
        finally:
            self.library.db.flush()

    @cherrypy.expose
    def query(self, object_type, query=None, include=None, offset=0, limit=0, sort=None):
        logger.debug("%s (%s)\tquery(object_type=%s, query=%s, include=%s, offset=%s, limit=%s, sort=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, object_type, query, include, offset, limit, sort, cherrypy.request.headers))
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if object_type not in ('artists', 'albums', 'songs'):
            raise cherrypy.HTTPError(501,'The requested option does not exist')
        retval = {'offset': offset, object_type: []}
        offset = int(offset)
        limit = int(limit)
        if query:
            query = shlex.split(query.lower())
        if include:
            include = include.lower().split(' ')
        if sort:
            sort = shlex.split(sort.lower())
        else:
            sort = ('albumartist', 'album', 'year', 'discnumber', 'tracknumber')
        tree = {}
        for item in self.library.cache.view('query/songs'):
            song = item['value']
            if query:
                match = True
                for term in query:
                    field = term.split(':', 1)
                    if len(field) == 1:
                        if term not in song['query']:
                            match = False
                            break
                    else:
                        field, word = field
                        if field not in song.keys():
                            match = False
                            break
                        else:
                            data = song[field]
                            if type(data) is not list:
                                data = [data]
                            if not data:
                                match = False
                                break
                            for entry in data:
                                if not fnmatch.fnmatch(unicode(entry).lower(), word):
                                    match = False
                                    break
                if not match:
                    continue
            try:
                del song['query']
            except:
                pass
            if object_type == 'songs':
                retval[object_type].append(song)
                continue
            if song.has_key('albumartist'):# and not (song['albumartist'].lower() in ('various', 'various artists', 'va')):
                artist = song['albumartist']
            else:
                artist = song['artist']
            if not tree.has_key(artist):
                tree[artist] = {}
            if not tree[artist].has_key(song['album']):
                tree[artist][song['album']] = []
            tree[artist][song['album']].append(song)
        if object_type in ('albums', 'artists'):
            artists = []
            for artist, albums in tree.iteritems():
                item = {'artist': artist}
                if (include and 'albums' in include) or object_type == 'albums':
                    item['albums'] = []
                    for album, songs in albums.iteritems():
                        album_item = {'album': album}
                        # fields = ('date', 'year', 'genre', 'totaltracks',
                        #           'tracktotal', 'totaldiscs', 'disctotal',
                        #           'compilation', 'albumartist')
                        fields = ('date', 'year')
                        for key in fields:
                            try:
                                album_item[key] = songs[0][key]
                            except:
                                continue
                        if include and ('songs' in include):
                            utils.complex_sort(album_item['songs'], *sort)
                        if album_item not in item['albums']:
                            item['albums'].append(album_item)
                    utils.complex_sort(item['albums'], *sort)
                elif include and ('songs' in include):
                    item['songs'] = []
                    for album, songs in albums.iteritems():
                        item['songs'] += songs
                    utils.complex_sort(item['songs'], *sort)
                artists.append(item)
            if object_type == 'albums':
                for artist in artists:
                    retval[object_type] += artist['albums']
                if include and ('artists' in include):
                    retval['artists'] = sorted(tree.keys())
            else:
                retval['artists'] = artists
        utils.complex_sort(retval[object_type], *sort)
        retval['total'] = len(retval[object_type])
        if limit:
            retval[object_type] = retval[object_type][offset:offset+limit]
        else:
            retval[object_type] = retval[object_type][offset:]
        return json.dumps(retval, indent=4)

    @cherrypy.expose
    def song(self, songid, bitrate=None):
        logger.debug("%s (%s)\tsong(songid=%s, bitrate=%s)\tHeaders: %s" % (utils.find_originating_host(cherrypy.request.headers), cherrypy.request.login, songid, bitrate, cherrypy.request.headers))
        try:
            songid, format = songid.split('.')
        except:
            format = None
        return self.get_song(songid, format, bitrate)


def start():
    """Starts the CherryPy web server"""

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

    if hasattr(cherrypy.engine, 'signal_handler'):
        cherrypy.engine.signal_handler.subscribe()
        del cherrypy.engine.signal_handler.handlers['SIGTERM']
        del cherrypy.engine.signal_handler.handlers['SIGHUP']

    try:
        cherrypy.engine.start()
    except IOError:
        logger.critical("It appears that another instance of Blofeld is already running. If you're sure this isn't the case, make sure nothing else is using port %s." % cfg['PORT'])


def block():
    try:
        while not shutting_down.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        stop()


def stop():
    transcoder.stop()
    library.stop()
    logger.debug("Stopping web server.")
    shutting_down.set()
    cherrypy.engine.exit()
