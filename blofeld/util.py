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
