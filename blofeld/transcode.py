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

from blofeld.config import *


def to_mp3(path):
    cherrypy.response.headers['Content-Type'] = 'audio/mpeg'
    def stream():
        ffmpeg = subprocess.Popen(
            [FFMPEG, '-i', path, '-f', 'mp3', '-ab', '160k', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=-1
            )
        try:
            yield ffmpeg.stdout.read(327680)
            yield ffmpeg.stdout.read()
        except: 
            print "\nTranscoding stopped or finished"
            yield None
    return stream();


def to_ogg(path):
    cherrypy.response.headers['Content-Type'] = 'audio/ogg'
    ffmpeg = subprocess.Popen(
        [FFMPEG, '-i', path, '-f', 'ogg', '-acodec', 'vorbis', '-aq', '40', '-'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        bufsize=-1
        )
    return ffmpeg.communicate()[0]
