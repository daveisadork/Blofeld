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
import sys
import unicodedata


def clean_text(text, encoding='utf-8'):
    """Convert a string or Unicode object to all lower case, and replace
    any odd characters with their searchable counterparts. For example, turn
    'M\xf6tley Cr\xfce' into u'motley crue'
    """
    # Make sure we have a unicode object to deal with
    if type(text) is not unicode:
        text = unicode(text, encoding)
    # Normalize our object to form KD, which replaces all compatibility
    # characters with their equivalents and then replace any odd characters in
    # our object with their easily searchable equivalent (e.g., substitute 'o'
    # for '\xf6') by encoding it to ASCII. I'm not sure if this is the right
    # way to go about doing this, but it works.
    text = unicodedata.normalize('NFKD',text)
    text = text.encode('ascii', 'ignore')
    # Since we just encoded the thing to ASCII, but we'd prefer to have
    # Unicode, let's convert it back.
    text = unicode(text.decode('ascii'))
    # Now let's make the whole thing lower case and return it
    text = text.lower()
    return text


def detectCPUs():
    """
    Detects the number of CPUs on a system. Cribbed from pp.
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
        if ncpus > 0:
            return ncpus
    return 1 # Default


def find_originating_host(headers):
    remote_add = ''
    if 'Remote-Addr' in headers:
        remote_add = headers['Remote-Addr']
    if 'X-Forwarded-For' in headers:
        remote_add = headers['X-Forwarded-For']
    if 'X-Real-IP' in headers:
        remote_add = headers['X-Real-IP']
    return remote_add


def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")


def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))

    return os.path.abspath(os.path.join(os.path.dirname(unicode(__file__, sys.getfilesystemencoding( ))), os.pardir, os.pardir))
    
