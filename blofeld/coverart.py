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

from blofeld.config import *


def resize_cover(songid, path, size):
    cover = 'Cover.jpg'
    uri = "file://" + urllib.pathname2url(os.path.join(path, cover))
    size = int(size)
    img_path = os.path.join(CACHE_DIR, str(size), songid + '.jpg')
    if not os.path.exists(os.path.split(img_path)[0]):
        os.makedirs(os.path.split(img_path)[0])
    try:
        artwork = urllib2.urlopen('file://' + urllib.pathname2url(img_path))
    except:
        image = Image.open(os.path.join(path, cover))
        if image.size[0] > size or image.size[1] > size:
            wpercent = (size/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((size,hsize), Image.ANTIALIAS)
            image.save(img_path)
            artwork = urllib2.urlopen('file://' + urllib.pathname2url(img_path))
        else:
            artwork = urllib2.urlopen(uri)
    return artwork


