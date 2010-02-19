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
import urllib
import urllib2

from urlparse import urlparse
from PIL import Image
import mutagen

from blofeld.config import *


def find_cover(location, songid=None):
    """Attempts to locate a cover image that would be associated with a given
    file.
    """
    # This block of code was for getting cover art embedded in the tags in the
    # file itself. So far, I haven't been able to make it work.
#    img_path = os.path.join(CACHE_DIR, songid + '.jpg')
#    if not os.path.exists(os.path.split(img_path)[0]):
#        os.makedirs(os.path.split(img_path)[0])
#    if os.path.exists(img_path):
#        return img_path
#    try:
#        metadata = mutagen.File(location)
#        for tag, value in metadata.iteritems():
#            if tag in ['coverart', 'WM/Picture', 'APIC:', 'covr']:
#                print type(value[0])
#                with open(img_path, 'w') as image:
#                    image.write(value[0])
#                print "Found an embedded image, using that one"
#                return img_path
#        return None
#    except:
#        return None
    # This list will hold the results of our search.
    images = []
    # Try to get the path to the folder containing the song for which we need
    # a cover.
    try:
        path = os.path.split(location)[0]
    except:
        return None
    # Look for any files in the path that are images and give them a score
    # based on their filename and append them to our results list.
    for item in os.listdir(path):
        name, extension = os.path.splitext(item)
        if extension.lower()[1:] in COVER_EXTENSIONS:
            score = 0
            if name.lower() in COVER_NAMES:
                score += 1
            images.append([score, os.path.join(path, item)])
    # Sort our images by score and return the highest one. Seems like a pretty
    # ham fisted approach, will need to refine this later.
    try:
        images.sort(reverse=True)
        for image in images:
            print "Score:", image[0], "Path:", image[1]
        return images[0][1]
    except:
        return None

def resize_cover(songid, cover, uri, size):
    """Resizes the cover image for a specific song to a given size and caches
    the resized image for any subsequent requests."""
    # This is the path to the resized image in the cache
    img_path = os.path.join(CACHE_DIR, str(size), songid + '.jpg')
    # This is a URI of the above path
    img_uri = 'file://' + urllib.pathname2url(img_path.encode(ENCODING))
    # Make sure our cache directory exists
    if not os.path.exists(os.path.split(img_path)[0]):
        os.makedirs(os.path.split(img_path)[0])
    try:
        # Try to create a file object pointing to the image in the cache
        artwork = urllib2.urlopen(img_uri)
    except:
        # Load the source image file with PIL
        image = Image.open(os.path.join(cover))
        # Check if the image is larger than what the client asked for. If it
        # is, we'll resize it. Otherwise we'll just send the original.
        if image.size[0] > size or image.size[1] > size:
            # Figure out the aspect ratio so we can maintain it
            wpercent = (size/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            # Resize the image
            image = image.resize((size,hsize), Image.ANTIALIAS)
            # Save it to the cache so we won't have to do this again.
            image.save(img_path)
            # Create a file object pointing to the image in the cache
            artwork = urllib2.urlopen(img_uri)
        else:
            artwork = urllib2.urlopen(uri)
    return artwork

COVER_EXTENSIONS = [
    "jpg",
    "png",
    "gif",
    "bmp"
]

COVER_NAMES = [
    "folder",
    "cover",
    "front",
    "coverart"
]
