import sys
import os
sys.stdout = sys.stderr
sys.path.insert(0, os.path.dirname(__file__))

import atexit
import cherrypy
from blofeld.config import *
from blofeld.log import logger, enable_file
from blofeld.web import WebInterface


enable_file()

if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
    cherrypy.engine.start(blocking=False)
    atexit.register(cherrypy.engine.stop)

cherrypy.config.update({
    'tools.encode.on': True, 
    'tools.encode.encoding': 'utf-8',
    'tools.gzip.on': True,
    'environment': 'embedded'
    })

static = {
    'tools.staticdir.on': True,
    'tools.staticdir.dir': os.path.join(THEME_DIR, 'static')
    }

conf = {
    '/static': static,
    '/blofeld/static': static
    }
    
cherrypy.server.unsubscribe()
application = cherrypy.Application(WebInterface(), script_name=None, config=conf)

