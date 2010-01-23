#!/usr/bin/env python

import os
import sys
from urlparse import urlparse
import urllib
import urllib2
import hashlib
import json
from Cheetah.Template import Template
import cherrypy
from cherrypy.lib.static import serve_file
from PIL import Image
import subprocess

try:
    from xml.etree.cElementTree import ElementTree
except:
    from xml.etree.ElementTree import ElementTree

import mimetypes 
mimetypes.init() 
program_dir = os.path.dirname(os.path.abspath(__file__))
database = "/home/dhayes/.local/share/rhythmbox/rhythmdb.xml"
#database = "/home/dhayes/Desktop/rhythmdb.xml"

class Blofeld:
    def __init__(self):
        self._path = os.path.dirname(os.path.abspath(__file__))
        print "Loading Rhythmbox database...",
        tree = ElementTree()
        tree.parse(database)
        self._entries = tree.findall("entry")
        self.songs = {}
        self.artists = {}
        self.albums = {}
        self.relationships = {}
        self.load_rhythmbox_db()

    def load_rhythmbox_db(self):
        for entry in self._entries:
            if entry.attrib['type'] == "song":
                location_hash = hashlib.sha1(entry.find('location').text.encode("utf-8")).hexdigest()
                self.songs[location_hash] = {}
                for element in entry:
                    tag = element.tag
                    try:
                        self.songs[location_hash][tag] = element.text
                    except:
                        self.songs[location_hash][tag] = ''
                    finally:
                        if tag == "artist":
                            artist_hash = hashlib.sha1(self.songs[location_hash][tag].encode("utf-8")).hexdigest()
                            self.songs[location_hash]['artist_hash'] = artist_hash
                            if artist_hash not in self.artists:
                                self.artists[artist_hash] = self.songs[location_hash][tag]
                        if tag == "album":
                            album_hash = hashlib.sha1(self.songs[location_hash][tag].encode("utf-8")).hexdigest()
                            self.songs[location_hash]['album_hash'] = album_hash
                            if album_hash not in self.albums:
                                self.albums[album_hash] = self.songs[location_hash][tag]
        for song_hash in self.songs:
            artist_hash = self.songs[song_hash]['artist_hash']
            album_hash= self.songs[song_hash]['album_hash']
            if artist_hash not in self.relationships:
                self.relationships[artist_hash] = {}
            if album_hash not in self.relationships[artist_hash]:
                self.relationships[artist_hash][album_hash] = []
            self.relationships[artist_hash][album_hash].append(song_hash)
        print "Done"

    def index(self):
        template = Template(file=os.path.join(self._path, 'templates/index.tmpl'))
        template.songs = self.songs
        return template.respond()
    index.exposed = True

    def list_albums(self, artists=None, query=None, output='json'):
        result = {}
        if artists:
            artists = artists.split(',')
            for artist in artists:
                for album in self.relationships[artist]:
                    result[album] = self.albums[album]
        if query:
            filter_result = {}
            if not result:
                result = self.albums
            for song in self.songs:
                if query.lower() in self.songs[song]['artist'].lower() and self.songs[song]['album_hash'] in result and self.songs[song]['album_hash'] not in filter_result:
                    filter_result[self.songs[song]['album_hash']] = self.songs[song]['album']
                elif query.lower() in self.songs[song]['album'].lower() and self.songs[song]['album_hash'] in result and self.songs[song]['album_hash'] not in filter_result:
                    filter_result[self.songs[song]['album_hash']] = self.songs[song]['album']
                elif query.lower() in self.songs[song]['title'].lower() and self.songs[song]['album_hash'] in result and self.songs[song]['album_hash'] not in filter_result:
                    filter_result[self.songs[song]['album_hash']] = self.songs[song]['album']
            result = filter_result
        if output == 'json':
            if result:
                return str(result)
            return str(self.albums)
        template = Template(file=os.path.join(self._path, 'templates/list_albums.tmpl'))
        if result:
            template.albums = result
        else: 
            template.albums = self.albums
        return template.respond()
    list_albums._cp_config = {'response.stream': True}
    list_albums.exposed = True

    def list_artists(self, query=None,  output='json'):
        result = {}
        if query:
            for song in self.songs:
                if query.lower() in self.songs[song]['artist'].lower() and self.songs[song]['artist_hash'] not in result:
                    result[self.songs[song]['artist_hash']] = self.songs[song]['artist']
                elif query.lower() in self.songs[song]['album'].lower() and self.songs[song]['artist_hash'] not in result:
                    result[self.songs[song]['artist_hash']] = self.songs[song]['artist']
                elif query.lower() in self.songs[song]['title'].lower() and self.songs[song]['artist_hash'] not in result:
                    result[self.songs[song]['artist_hash']] = self.songs[song]['artist']
        if output == 'json':
            if result:
                return str(result)
            else:
                return str(self.artists)
        template = Template(file=os.path.join(self._path, 'templates/list_artists.tmpl'))
        if result:
            template.artists = result
        else:
            template.artists = self.artists
        return template.respond()
    list_artists._cp_config = {'response.stream': True}
    list_artists.exposed = True

    def list_songs(self, artists=None, albums=None, query=None,  output='json'):
        result = {}
        if albums and not artists:
            albums = albums.split(',')
            for album in albums:
                for artist in self.relationships:
                    if album in self.relationships[artist]:
                        for song in self.relationships[artist][album]:
                            result[song] = self.songs[song]
        if artists and not albums:
            artists = artists.split(',')
            for artist in artists:
                for album in self.relationships[artist]:
                    for song in self.relationships[artist][album]:
                        result[song] = self.songs[song]
        if (artists != None) and (albums != None):
            artists = artists.split(',')
            albums = albums.split(',')
            for album in albums:
                for artist in artists:
                    try:
                        for song in self.relationships[artist][album]:
                            result[song] = self.songs[song]
                    except:
                        pass
        if query:
            filter_result = {}
            if not result:
                result = self.songs
            for song in result:
                if query.lower() in result[song]['artist'].lower() and song not in filter_result:
                    filter_result[song] = result[song]
                elif query.lower() in result[song]['album'].lower() and song not in filter_result:
                    filter_result[song] = result[song]
                elif query.lower() in result[song]['title'].lower() and song not in filter_result:
                    filter_result[song] = result[song]
            result = filter_result
        if output =='json':
            return str(result)
        template = Template(file=os.path.join(self._path, 'templates/list_songs.tmpl'))
        template.songs = result
        return template.respond()
    list_songs._cp_config = {'response.stream': True}
    list_songs.exposed = True

    def get_song(self, songid=None, download=False, format=None):
        if songid not in self.songs:
            return "False"
        uri = self.songs[songid]['location']
        path = urllib.url2pathname(urlparse(uri).path)
        song = urllib2.urlopen(uri)
        print song.info()['Content-Type']
        if download:
            return serve_file(path, song.info()['Content-Type'], os.path.split(path)[1])
        if format != None:
            return self.transcode(path, song, format)
        else:
            cherrypy.response.headers['Content-Type'] = song.info()['Content-Type']
            return song.read()
        return False
    get_song.exposed = True
    get_song._cp_config = {'response.stream': True}

    def transcode(self, path, song, format):
        if format == 'mp3':
            cherrypy.response.headers['Content-Type'] = 'audio/mpeg'
            if song.info()['Content-Type'] == 'audio/mpeg':
                return song.read()
            ffmpeg = subprocess.Popen(['/usr/bin/ffmpeg', '-i', path, '-f', 'mp3', '-ab', '160k', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=-1)
            def stream():
                try:
                    print "\nreading initial data"
                    yield ffmpeg.stdout.read(327680)
                    print "\nreading remaining data"
                    yield ffmpeg.stdout.read()
                except: 
                    print "\nTranscoding stopped or finished"
                    return
            return stream();
        if format == 'ogg':
            cherrypy.response.headers['Content-Type'] = 'audio/ogg'
            if song.info()['Content-Type'] == 'audio/ogg':
                return song.read()
            ffmpeg = subprocess.Popen(['/usr/bin/ffmpeg', '-i', path, '-f', 'ogg', '-acodec', 'vorbis', '-aq', '40', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=-1)
            return ffmpeg.communicate()[0]

    def get_cover(self, songid=None, size='original', download=False):
        if songid not in self.songs:
            return "Can't find that song."
        uri = self.songs[songid]['location']
        path = os.path.split(urllib.url2pathname(urlparse(uri).path))[0]
        cover = 'Cover.jpg'
        artwork = urllib2.urlopen('file://' + urllib.pathname2url(os.path.join(path, cover)))
        if download:
            return serve_file(os.path.join(path, cover), artwork.info()['Content-Type'], cover)
        if size != 'original':
            size = int(size)
            img_path = os.path.join(program_dir + '/cache', songid + '-' + str(size) + '.jpg')
            try:
                artwork = urllib2.urlopen('file://' + urllib.pathname2url(img_path))
            except:
                image = Image.open(os.path.join(path, cover))
                if image.size[0] > size or image.size[1] > size:
                    wpercent = (size/float(image.size[0]))
                    hsize = int((float(image.size[1])*float(wpercent)))
                    image = image.resize((size,hsize), Image.ANTIALIAS)
                    image.save(os.path.join(urllib.pathname2url(img_path)))
                    artwork = urllib2.urlopen('file://' + urllib.pathname2url(img_path))
                else:
                    artwork = urllib2.urlopen('file://' + urllib.pathname2url(os.path.join(path, cover)))
        else:
            artwork = urllib2.urlopen('file://' + urllib.pathname2url(os.path.join(path, cover)))
        cherrypy.response.headers['Content-Type'] = artwork.info()['Content-Type']
        return artwork.read()
        #return serve_file(os.path.join(path, cover), f.info()['Content-Type'], cover)
    get_cover.exposed = True

if __name__ == '__main__':
    
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'tools.encode.on':True, 
        'tools.encode.encoding':'utf-8'
        })

    conf = {
        '/assets': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(program_dir, 'assets')}
        }
    if not os.path.isdir(os.path.join(program_dir, 'cache')):
        os.mkdir(os.path.join(program_dir, 'cache'))
    cherrypy.quickstart(Blofeld(), '/', config=conf)

