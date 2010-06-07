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
import logging
import logging.handlers

from blofeld.config import cfg

__all__ = ['logger', 'enable_file', 'enable_single_file', 'enable_console']

logger = logging.getLogger("Blofeld")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARN,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def enable_file(log_file=os.path.join(cfg['LOG_DIR'], "blofeld.log")):
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=1048576, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def enable_single_file(path):
    fh = logging.FileHandler(path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def enable_console(level='warn'):
    ch = logging.StreamHandler()
    ch.setLevel(log_levels[level])
    ch.setFormatter(formatter)
    logger.addHandler(ch)


# "application" code
#logger.debug("debug message")
#logger.info("info message")
#logger.warn("warn message")
#logger.error("error message")
#logger.critical("critical message")
