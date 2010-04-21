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

import sys, gobject, glib
import subprocess
import time

#from blofeld.config import *
import pygst
import gst


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


def gst_mp3(path):
    pipeline = gst.Pipeline("pipeline")
    filesrc = gst.element_factory_make("filesrc", "filesrc")
    decoder = gst.element_factory_make("decodebin", "decoder")
    converter = gst.element_factory_make("audioconvert", "converter")
    encoder = gst.element_factory_make("lamemp3enc", "encoder")
    muxer = gst.element_factory_make("id3v2mux", "muxer")
    output = gst.element_factory_make("appsink", "output")


class TranscodeGstreamer:

    def __init__(self, path):
        print "Transcoding", path
        self.path = path
        self.pipeline = gst.Pipeline("pipeline")
        self.source = gst.element_factory_make("filesrc", "source")
        self.decoder = gst.element_factory_make("decodebin", "decoder")
        self.decoder.connect("pad-added", self.decoder_callback)
        self.converter = gst.element_factory_make("audioconvert", "converter")
        self.encoder = gst.element_factory_make("lamemp3enc", "encoder")
        self.muxer = gst.element_factory_make("id3v2mux", "muxer")
        self.output = gst.element_factory_make("appsink", "output")
        self.source.set_property("location", self.path)
        self.output.set_property("sync", False)
        self.pipeline.add(self.source, self.decoder, self.converter, self.encoder, self.muxer, self.output)
        gst.element_link_many(self.source, self.decoder)
        gst.element_link_many(self.converter, self.encoder, self.muxer, self.output)
#        bus = self.pipeline.get_bus()
#        bus.add_signal_watch()
#        bus.connect("message", self.on_message)


#    def on_message(self, bus, message):
#        t = message.type
#        if t == gst.MESSAGE_EOS:
#            self.pipeline.set_state(gst.STATE_NULL)
#            self.playmode = False
#            print "we're done apparently"
#        elif t == gst.MESSAGE_ERROR:
#            self.pipeline.set_state(gst.STATE_NULL)
#            err, debug = message.parse_error()
#            print "Error: %s" % err, debug
#            self.playmode = False

    def start(self):
        print "Starting, setting playmode to True"
        self.playmode = True
        self.pipeline.set_state(gst.STATE_PLAYING)
        while not self.output.get_property("eos"):
            yield str(self.output.emit('pull-buffer'))
        self.pipeline.set_state(gst.STATE_NULL)
        print "Guess we're finished"


    def decoder_callback(self, decoder, pad):
        adec_pad = self.converter.get_pad("sink")
        pad.link(adec_pad)


if __name__ == "__main__":
    transcoder = TranscodeGstreamer("/home/dave/Desktop/Audioslave - Audioslave - 01 - Cochise.ogg")
    thread.start_new_thread(transcoder.start, ())
    gobject.threads_init()
    loop = glib.MainLoop()
    loop.run()



# gst-launch-0.10 filesrc location=/home/dave/Music/Katy\ Perry/One\ of\ the\ Boys/Katy\ Perry\ -\ One\ of\ the\ Boys\ -\ 02\ -\ I\ Kissed\ a\ Girl.mp3 ! decodebin ! audioconvert ! vorbisenc ! oggmux ! filesink location=test.ogg

# gst-launch-0.10 filesrc location=Audioslave\ -\ Audioslave\ -\ 01\ -\ Cochise.ogg ! decodebin ! audioconvert ! lamemp3enc ! id3v2mux ! filesink location=test.mp3
