bin_SCRIPTS = blofeld
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = blofeld.in

do_subst = sed -e 's,[@]PYTHON[@],$(PYTHON),g' \
		   -e 's,[@]pkgdatadir[@],$(pkgdatadir),g'

blofeld: blofeld.in Makefile
	$(do_subst) < $(srcdir)/blofeld.in > blofeld
	chmod +x blofeld

## File created by the gnome-build tools
