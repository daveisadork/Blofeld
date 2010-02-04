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
import subprocess

import cherrypy
from cherrypy.lib.static import serve_file

def transcode(path, song, format):
    if format == 'mp3':
        if song.info()['Content-Type'] == 'audio/mpeg':
            return serve_file(path, 'audio/mpeg', "inline",
                              os.path.split(path)[1])
        cherrypy.response.headers['Content-Type'] = 'audio/mpeg'
        ffmpeg = subprocess.Popen(
            ['/usr/bin/ffmpeg',  '-i', path, '-f', 'mp3', '-ab', '160k', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=-1
            )
        def stream():
            try:
                print "\nreading initial data"
                yield ffmpeg.stdout.read(327680)
                print "\nreading remaining data"
                yield ffmpeg.stdout.read()
                return 
            except: 
                print "\nTranscoding stopped or finished"
                return
        return stream();
    if format == 'ogg':
        cherrypy.response.headers['Content-Type'] = 'audio/ogg'
        if song.info()['Content-Type'] == 'audio/ogg':
            return serve_file(path, 'audio/ogg', "inline",
                              os.path.split(path)[1])
        ffmpeg = subprocess.Popen(
            ['/usr/bin/ffmpeg', '-i', path, '-f', 'ogg', '-acodec', 'vorbis', '-aq', '40', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=-1
            )
        return ffmpeg.communicate()[0]
