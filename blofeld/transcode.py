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

from blofeld.config import *


def to_mp3(path):
    """Transcodes a file to MP3 and streams it to the client in 320kb chunks"""
    # Define a generator so we can yield 320kb chunks of the encoder output
    def stream():
        # Spawn the FFMPEG process to do the transcoding
        ffmpeg = subprocess.Popen(
            [FFMPEG,
                '-i', path,
                '-f', 'mp3',
                '-ab', '160k',
                '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=-1
            )
        try:
            # Read 320kb of data from the encoder
            chunk = ffmpeg.stdout.read(327680)
            # Make sure there is actually data, and then yield it. Continue 
            # doing so until we run out of data, which means the transcoder
            # has stopped.
            while chunk != '':
                yield chunk
                chunk = ffmpeg.stdout.read(327680)
            print "\nTranscoding seems to be finished"
            # This somehow stops us from ending up with a zombie
            ffmpeg.wait()
            return
        except: 
            print "\nTranscoding stopped for some reason"
            # This somehow stops us from ending up with a zombie
            ffmpeg.wait()
            return
    # Start our generator and return its output
    return stream();


def to_vorbis(path):
    """Transcodes a file to OGG and streams it to the client in 320kb chunks"""
    # Define a generator so we can yield 320kb chunks of the encoder output
    def stream():
        # Spawn the FFMPEG process to do the transcoding
        ffmpeg = subprocess.Popen(
            [FFMPEG,
                '-i', path,
                '-f', 'ogg',
                '-acodec', 'vorbis',
                '-aq', '40',
                '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=-1
            )
        try:
            # Read 320kb of data from the encoder
            chunk = ffmpeg.stdout.read(327680)
            # Make sure there is actually data, and then yield it. Continue 
            # doing so until we run out of data, which means the transcoder
            # has stopped.
            while chunk != '':
                yield chunk
                chunk = ffmpeg.stdout.read(327680)
            print "\nTranscoding seems to be finished"
            # This somehow stops us from ending up with a zombie
            ffmpeg.wait()
            return
        except: 
            print "\nTranscoding stopped for some reason"
            # This somehow stops us from ending up with a zombie
            ffmpeg.wait()
            return
    # Start our generator and return its output
    return stream()


def transcode_gstreamer(path):
    pass
