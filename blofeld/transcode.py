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


import sys
import time
from multiprocessing import Process, Pipe

import pygst
pygst.require('0.10')
import gst

from blofeld.log import logger

def transcode_process(conn, path, format='mp3', bitrate=False):
    # If we were passed a bitrate argument, make sure it's actually a number
    try:
        bitrate = int(bitrate)
    except:
        bitrate = False
    log_message = "Transcoding %s to %s" % (path, format)
    # Create our transcoding pipeline using one of the strings at the end of
    # this module.
    transcoder = gst.parse_launch(pipeline[format])
    # Set the bitrate we were asked for
    if bitrate in [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192,
                                                                224, 256, 320]:
        log_message += " at %d kbps" % bitrate
        encoder = transcoder.get_by_name('encoder')
        muxer = transcoder.get_by_name('muxer')
        if format is 'mp3':
            encoder.set_property("target", "bitrate")
            encoder.set_property("bitrate", bitrate)
        elif format is 'ogg':
            encoder.set_property("max-bitrate", bitrate * 1024)
        elif format is 'm4a':
            encoder.set_property("bitrate", bitrate * 1000)
            #encoder.set_property("outputformat", 1)
            #encoder.set_property("profile", 1)
            #muxer.set_property("faststart", True)
    # Load our file into the transcoder
    logger.info(log_message + ".")
    source = transcoder.get_by_name('source')
    source.set_property("location", path)
    # Set the output to be asynchronous so the transcoding happens as quickly
    # as possible rather than real time.
    output = transcoder.get_by_name('output')
    output.set_property("sync", False)
    # Start the pipeline running so we can start grabbing data out of it
    transcoder.set_state(gst.STATE_PLAYING)
    transcoder.get_state()
    try:
        # Grab a bit of encoded data and yield it to the client
        while True:
            output_buffer = output.emit('pull-buffer')
            if output_buffer:
                conn.send(output_buffer.data)
            else:
                break
    except:
        logger.warn("Some type of error occured during transcoding.")
    finally:
        conn.send(False)
        conn.close()
        # I think this is supposed to free the memory used by the transcoder
        transcoder.set_state(gst.STATE_NULL)

def transcode(path, format='mp3', bitrate=False):
    try:
        start_time = time.time()
        parent_conn, child_conn = Pipe()
        process = Process(target=transcode_process, args=(child_conn, path, format, bitrate))
        process.start()
        while True:
            data = parent_conn.recv()
            if not data:
                break
            yield data
    except GeneratorExit:
        process.terminate()
        logger.debug("User canceled the request during transcoding.")
    except:
        logger.warn("Some type of error occured during transcoding.")
    finally:
        parent_conn.close()
        process.join()
        logger.debug("Transcoded %s in %0.2f seconds." % (path, time.time() - start_time))

# These are the transcoding pipelines we can use. I should probably add more
pipeline = {
    # id3v2mux would be preferable because it transfers embedded cover art, but
    # stupid jPlayer chokes on its output so we have to use id3mux instead.
    #'mp3': "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! id3v2mux ! appsink name=output",
    'mp3': "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! id3mux name=muxer ! appsink name=output",
    'ogg': "filesrc name=source ! decodebin ! audioconvert ! vorbisenc name=encoder ! oggmux name=muxer ! appsink name=output",
    'm4a': "filesrc name=source ! decodebin ! audioconvert ! ffenc_aac name=encoder ! ffmux_mp4 name=muxer ! appsink name=output"
}

# The win32 port of gstreamer apparently doesn't have id3mux or id3v2mux so we have to use 
# ffmux_mp3 instead.
if sys.platform == "win32":
    pipeline['mp3'] = "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! ffmux_mp3 name=muxer ! appsink name=output"
