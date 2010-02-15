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
    images = []
    try:
        path = os.path.split(location)[0]
    except:
        return None
    for item in os.listdir(path):
        name, extension = os.path.splitext(item)
        if extension.lower()[1:] in COVER_EXTENSIONS:
            score = 0
            if name.lower() in COVER_NAMES:
                score += 1
            images.append([score, os.path.join(path, item)])
    try:
        images.sort(reverse=True)
        for image in images:
            print "Score:", image[0], "Path:", image[1]
        return images[0][1]
    except:
        return None

def resize_cover(songid, cover, uri, size):
    img_path = os.path.join(CACHE_DIR, str(size), songid + '.jpg')
    img_uri = 'file://' + urllib.pathname2url(img_path.encode(ENCODING))
    if not os.path.exists(os.path.split(img_path)[0]):
        os.makedirs(os.path.split(img_path)[0])
    try:
        artwork = urllib2.urlopen(img_uri)
    except:
        image = Image.open(os.path.join(cover))
        if image.size[0] > size or image.size[1] > size:
            wpercent = (size/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((size,hsize), Image.ANTIALIAS)
            image.save(img_path)
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
