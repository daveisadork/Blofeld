## Process this file with automake to produce Makefile.in
## Created by Anjuta

blofelddocdir = ${prefix}/doc/blofeld
blofelddoc_DATA = \
	README\
	COPYING\
	INSTALL\

EXTRA_DIST = $(blofelddoc_DATA)

SUBDIRS = \
	scripts\
	blofeld

Blofeld_PYTHON = \
	Blofeld.py

Blofelddir = \
	$(pkgdatadir)

# Remove doc directory on uninstall
uninstall-local:
	-rm -r $(blofelddocdir)
