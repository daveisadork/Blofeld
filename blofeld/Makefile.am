CLEANFILES = version.py
EXTRA_DIST = version.py.in

SUBDIRS = library

blofeld_PYTHON = \
    config.py\
    coverart.py\
    download.py \
    __init__.py \
    log.py \
    playlist.py \
    transcode.py \
    utils.py \
    web.py \
    version.py

blofelddir = \
    $(pkgpythondir)

GIT_REVISION := $(shell if [ -d "../.git" ]; then git shortlog | grep -E '^[ ]+\w+' | wc -l; else echo "unknown"; fi)

do_subst = sed -e 's,[@]PACKAGE_VERSION[@],$(PACKAGE_VERSION),g' \
               -e 's,[@]GIT_REVISION[@],$(GIT_REVISION),g'

version.py: version.py.in Makefile
	$(do_subst) < $(srcdir)/version.py.in > version.py

## File created by the gnome-build tools

