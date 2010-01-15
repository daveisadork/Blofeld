#!/usr/bin/env python

import os
import sys
import cherrypy

class HelloWorld:
    def index(self):
        return os.listdir('/home/dhayes/Music')
    index.exposed = True

cherrypy.quickstart(HelloWorld())
