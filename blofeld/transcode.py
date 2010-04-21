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


import time

import pygst
import gst


def transcode(path, format='mp3', bitrate=False):
    start_time = time.time()
    try:
        bitrate = int(bitrate)
    except:
        bitrate = False
    print "Transcoding", path
    transcoder = gst.parse_launch(pipeline[format])
    if bitrate in [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]:
        print "Setting bitrate to", bitrate, "kbps"
        encoder = transcoder.get_by_name('encoder')
        if format is 'mp3':
            encoder.set_property("target", "bitrate")
            encoder.set_property("bitrate", bitrate)
        elif format is 'ogg':
            encoder.set_property("max-bitrate", bitrate * 1024)
    source = transcoder.get_by_name('source')
    source.set_property("location", path)
    output = transcoder.get_by_name('output')
    output.set_property("sync", False)
    transcoder.set_state(gst.STATE_PLAYING)
    while not output.get_property("eos"):
        yield str(output.emit('pull-buffer'))
    transcoder.set_state(gst.STATE_NULL)
    print "Guess we're finished.", time.time() - start_time, "seconds."


pipeline = {
    'mp3': "filesrc name=source ! decodebin ! audioconvert ! lamemp3enc name=encoder ! id3v2mux ! appsink name=output",
    'ogg': "filesrc name=source ! decodebin ! audioconvert ! vorbisenc name=encoder ! oggmux ! appsink name=output"
}
