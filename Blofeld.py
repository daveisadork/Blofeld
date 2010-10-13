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
import sys
from optparse import OptionParser


def get_options():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config",
                      action="store", type="string", dest="config_file",
                      help="Load a specific configuration file.")
    parser.add_option("-l", "--logfile",
                      action="store", type="string", dest="log_file",
                      help="Output logging to a specific file.")
    #parser.add_option("-m", "--music",
    #                  action="store", type="string", dest="music_dir",
    #                    help="Load music from a certain directory.")
    parser.add_option("-d", "--daemonize",
                      action="store_true", dest="daemonize", default=False,
                      help="Detach from the console and run in the background")
    parser.add_option("--debug",
                      action="store_true", dest="debug", default=False,
                      help="Show debug output (identical to logfiles)")
    parser.add_option("--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Show additional informational messages")
    parser.add_option("--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="Show no console output at all")
    parser.add_option("--cherrypy",
                      action="store_true", dest="cherrypy", default=False,
                      help="Show CherryPy's console messages")
    return parser.parse_args()


def daemonize(name):
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            #print "Daemon PID %d" % pid 
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 

    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(name)+1)
    buff.value = name
    libc.prctl(15, byref(buff), 0, 0, 0)


if __name__ == "__main__":
    (options, args) = get_options()
    if options.daemonize:
        daemonize(sys.argv[0])
    from blofeld.config import cfg
    cfg.__init__(installed=os.getenv('BLOFELD_INSTALLED'),
                 system=os.getenv('BLOFELD_SYSTEM_WIDE'),
                 program_dir=os.path.abspath(os.path.dirname(__file__)),
                 path=options.config_file
                 )
    from blofeld.log import *
    if options.log_file:
        enable_single_file(options.log_file)
    else:
        enable_file()
    if options.daemonize:
        pass
    elif options.debug:
        enable_console('debug')
    elif options.verbose:
        enable_console('info')
    elif options.quiet:
        enable_console('critical')
    else:
        enable_console()
    cfg['CHERRYPY_OUTPUT'] = options.cherrypy
    import blofeld.web
    blofeld.web.start()
