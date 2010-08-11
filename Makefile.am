## Process this file with automake to produce Makefile.in
## Created by Anjuta

blofelddocdir = ${prefix}/doc/blofeld
blofelddoc_DATA = \
	README\
	COPYING\
	AUTHORS\
	ChangeLog\
	INSTALL\
	NEWS


EXTRA_DIST = $(blofelddoc_DATA)

SUBDIRS = \
	scripts\
	blofeld

Blofelddir = \
	$(pkgdatadir)

Blofeld_PYTHON = \
	Blofeld.py

# Remove doc directory on uninstall
uninstall-local:
	-rm -r $(blofelddocdir)
