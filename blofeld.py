#!/usr/bin/env python


import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import urllib2
import hashlib
import json
from Cheetah.Template import Template
import cherrypy
try:
    from xml.etree.cElementTree import ElementTree
except:
    from xml.etree.ElementTree import ElementTree

import mimetypes 
mimetypes.init() 

database = "/home/dhayes/.local/share/rhythmbox/rhythmdb.xml"

class GetMusicList:
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
        for entry in self._entries:
            if entry.attrib['type'] == "song":
                location_hash = hashlib.sha1(entry.find('location').text).hexdigest()
                self.songs[location_hash] = {}
                for element in entry:
                    tag = element.tag
                    try:
                        self.songs[location_hash][tag] = element.text
                    except:
                        self.songs[location_hash][tag] = ''
                    finally:
                        if tag == "artist":
                            artist_hash = hashlib.sha1(self.songs[location_hash][tag]).hexdigest()
                            self.songs[location_hash]['artist_hash'] = artist_hash
                            if artist_hash not in self.artists:
                                self.artists[artist_hash] = self.songs[location_hash][tag]
                        if tag == "album":
                            album_hash = hashlib.sha1(self.songs[location_hash][tag]).hexdigest()
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

    def list_albums(self, artists=None, search_term=None, output='json'):
        result = None
        if artists:
            artists = artists.split(',')
            result = {}
            for artist in artists:
                for album in self.relationships[artist]:
                    result[album] = self.albums[album]
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
    list_albums.exposed = True

    def list_artists(self, search_term=None,  output='json'):
        if output == 'json':
            return str(self.artists)
        template = Template(file=os.path.join(self._path, 'templates/list_artists.tmpl'))
        template.artists = self.artists
        return template.respond()
    list_artists.exposed = True

    def list_songs(self, artists=None, albums=None, search_term=None,  output='json'):
        result = None
        if albums and not artists:
            albums = albums.split(',')
            result = {}
            for album in albums:
                for artist in self.relationships:
                    if album in self.relationships[artist]:
                        for song in self.relationships[artist][album]:
                            result[song] = self.songs[song]
        if artists and not albums:
            artists = artists.split(',')
            result = {}
            for artist in artists:
                for album in self.relationships[artist]:
                    for song in self.relationships[artist][album]:
                        result[song] = self.songs[song]
        if (artists != None) and (albums != None):
            result = {}
            artists = artists.split(',')
            albums = albums.split(',')
            for artist in artists:
                for album in albums:
                    for song in self.relationships[artist][album]:
                        result[song] = self.songs[song]
        if output =='json':
            if result != None:
                return str(result)
            return "too many songs"
        template = Template(file=os.path.join(self._path, 'templates/list_songs.tmpl'))
        if result != None:
            template.songs = result
        else: 
            return "too many songs"
        return template.respond()
    list_songs.exposed = True

    def get_song(self, songid=None):
        if songid not in self.songs:
            return "Can't find that song."
        f = urllib2.urlopen(self.songs[songid]['location'])
        cherrypy.response.headers['Content-Type'] = f.info()['Content-Type']
        read_data = f.read()
        return read_data
    get_song.exposed = True

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'tools.encode.on':True, 
        'tools.encode.encoding':'utf8'
        })

    conf = {
        '/assets': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(current_dir, 'assets')}
        }

    cherrypy.quickstart(GetMusicList(), '/', config=conf)

