#!/usr/bin/env python

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


try:
    from blofeld.version import __version__, __revision__
    release = True
except:
    release = False
    try:
        with open(os.path.abspath('.git/HEAD'), 'r') as head:
            data = head.readline()
        __version__ = data.split('/')[-1][:-1]
        with open(os.path.abspath('.git/logs/HEAD'), 'r') as log:
            data = log.readlines()
        __revision__ = data[-1].split(' ')[1]
    except:
        __version__ = "unknown"
        __revision__ = "unknown"
