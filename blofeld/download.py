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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSEh.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import zipfile
import hashlib

from blofeld.log import logger
from blofeld.config import cfg
from blofeld.coverart import find_cover


def create_archive(songs):
    try:
        files = []
        for song in songs:
            location = song['location'].encode('utf8')
            print type(location)
            zip_path = song['location'].replace(cfg['MUSIC_PATH'], '').encode('utf8')
            files.append((location, zip_path))
            zip_cover_path = os.path.join(os.path.dirname(zip_path), 'Cover.jpg')
            cover = (find_cover(song), zip_cover_path)
            if cover not in files:
                files.append(cover)
        path = os.path.join(cfg['CACHE_DIR'],
                            '%s.zip') % hashlib.sha1(str(files)).hexdigest()
        logger.debug("Creating archive at %s" % path)
        logger.debug(files)
        archive = zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED)
        for item in files:
            logger.debug('Added "%s" to "%s"' % item)
            archive.write(*item)
        archive.close()
        return path
    except Exception as e:
        logger.exception(e)
