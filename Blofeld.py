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
import signal
from multiprocessing import freeze_support
from optparse import OptionParser

try:
    import cPickle as pickle
except:
    import pickle
from blofeld.utils import *


def get_options():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--version",
                      action="store_true", dest="version",
                      help="Print the version number and exit.")
    parser.add_option("-b", "--base_dir",
                      action="store", type="string", dest="base_dir",
                      help="Base directory for storing cache, logs, etc.")
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


def set_exit_handler(func):
    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception("pywin32 not installed for Python " + version)
    else:
        signal.signal(signal.SIGTERM, func)
        signal.signal(signal.SIGHUP, func)


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
    os.chdir(".")
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


def shutdown(sig=signal.SIGTERM, func=None):
    if sig is signal.SIGTERM:
        logger.info("Received SIGTERM, shutting down.")
    else:
        logger.info("User pressed Ctrl+C, shutting down.")
    blofeld.web.stop()


if __name__ == "__main__":
    freeze_support()
    (options, args) = get_options()
    if options.version:
        import blofeld
        if blofeld.release:
            print "Blofeld v%s" % blofeld.__version__
        else:
            print "Blofeld git branch %s, commit %s" % (blofeld.__version__, blofeld.__revision__)
        sys.exit()
    if options.daemonize:
        if os.name == "nt":
            print "The daemonize option is not available on your OS."
            sys.exit()
        daemonize(sys.argv[0])
    from blofeld.config import cfg
    cfg.__init__(base_dir=options.base_dir, path=options.config_file)
    cfg.load_config()
    if os.path.exists(cfg['PID_FILE']):
        with open(cfg['PID_FILE'], "r") as pidfile:
            state = pickle.load(pidfile)
        if state['pid'] == os.getpid():
            print "Blofeld is already running."
            sys.exit()
        else:
            os.remove(cfg['PID_FILE'])
            del cfg
            from blofeld.config import cfg
            cfg.__init__(base_dir=options.base_dir, path=options.config_file)
            cfg.load_config()
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
    logger.debug("Logging initialized.")
    set_exit_handler(shutdown)
    logger.debug("Configuring the web server.")
    cfg['CHERRYPY_OUTPUT'] = options.cherrypy
    logger.debug("Writing PID file.")
    with open(cfg['PID_FILE'], "w") as pidfile:
        pickle.dump({'cfg': cfg, 'options': options, 'args': args, 'pid': os.getpid()}, pidfile)
    logger.info("Starting web server at %s:%s" % (cfg['HOSTNAME'], cfg['PORT']))
    try:
        import blofeld.web
        blofeld.web.start()
        set_exit_handler(shutdown)
        blofeld.web.block()
    except KeyboardInterrupt:
        if not os.name == "nt":
            shutdown()
    logger.debug("The web server has stopped.")
    logger.debug("Removing PID file.")
    try:
        os.remove(cfg['PID_FILE'])
    except:
        pass
    sys.exit()

