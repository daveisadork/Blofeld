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
import time
from multiprocessing import Event, Process, Pipe
from Queue import Queue

from blofeld.config import cfg
from blofeld.log import logger


def transcode_process(conn, path, stop, format='mp3', bitrate=False):
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import GObject, Gst

    GObject.threads_init()
    Gst.init(None)

    # If we were passed a bitrate argument, make sure it's actually a number
    try:
        bitrate = int(bitrate)
    except:
        bitrate = False
    log_message = "Transcoding %s to %s" % (path.encode(cfg['ENCODING']), format)
    # Create our transcoding pipeline using one of the strings at the end of
    # this module.
    transcoder = Gst.parse_launch(pipeline[format])
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
    log_message += "."
    logger.info(log_message)
    source = transcoder.get_by_name('source')
    try:
        source.set_property("location", path.encode('utf-8'))
        # Set the output to be asynchronous so the transcoding happens as quickly
        # as possible rather than real time.
        output = transcoder.get_by_name('output')
        output.set_property("sync", False)
        # Start the pipeline running so we can start grabbing data out of it
        transcoder.set_state(Gst.State.PLAYING)
        #transcoder.get_state()
        try:
            # Grab a bit of encoded data and yield it to the client
            while True:
                sample = output.emit('pull-sample')
                if sample and not stop.is_set():
                    buf = sample.get_buffer()
                    data = buf.extract_dup(0, buf.get_size())
                    conn.send(data)
                else:
                    break
        except Exception as e:
            logger.warn(str(e))
            logger.warn("Some type of error occured during transcoding.")
    except Exception as e:
        logger.error(str(e))
        logger.error("Could not open the file for transcoding. This is probably happening because there are non-ASCII characters in the filename.")
    finally:
        try:
            # I think this is supposed to free the memory used by the transcoder
            transcoder.set_state(Gst.State.NULL)
        except:
            pass
        if not stop.is_set():
            conn.send(False)
            conn.close()

class Transcoder:
    def __init__(self):
        self.stopping = Event()

    def stop(self):
        logger.debug("Preventing new transcoding processes.")
        self.stopping.set()

    def transcode(self, path, format='mp3', bitrate=False):
        if self.stopping.is_set():
            return
        try:
            stop = Event()
            start_time = time.time()
            parent_conn, child_conn = Pipe()
            process = Process(target=transcode_process,
                    args=(child_conn, path, stop, format, bitrate))
            process.start()
            while not (self.stopping.is_set() or stop.is_set()):
                data = parent_conn.recv()
                if not data:
                    break
                yield data
            logger.debug("Transcoded %s in %0.2f seconds." % (path.encode(cfg['ENCODING']), time.time() - start_time))
        except GeneratorExit:
            stop.set()
            logger.debug("User canceled the request during transcoding.")
        except:
            stop.set()
            logger.warn("Some type of error occured during transcoding.")
        finally:
            parent_conn.close()
            process.join()

# These are the transcoding pipelines we can use. I should probably add more
pipeline = {
    # id3v2mux would be preferable because it transfers embedded cover art, but
    # stupid jPlayer chokes on its output so we have to use id3mux instead.
    #'mp3': "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! id3v2mux ! appsink name=output",
    'mp3': "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! id3mux name=muxer ! appsink name=output",
    'ogg': "filesrc name=source ! decodebin ! audioconvert ! vorbisenc name=encoder ! oggmux name=muxer ! appsink name=output",
    'm4a': "filesrc name=source ! decodebin ! audioconvert ! avenc_aac name=encoder ! avmux_mp4 name=muxer ! appsink name=output"
}

# The win32 port of gstreamer apparently doesn't have id3mux or id3v2mux so we have to use
# ffmux_mp3 instead.
if os.name == "nt":
    pipeline['mp3'] = "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! avmux_mp3 name=muxer ! appsink name=output"
