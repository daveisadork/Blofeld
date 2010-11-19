#!/usr/bin/env python -OO
#
# Copyright 2008-2010 The Blofeld-Team <team@blofeld.org>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from distutils.core import setup

import glob
import sys
import os
import platform
import tarfile
import re
import subprocess
import shutil
try:
    import py2exe
except ImportError:
    py2exe = None
try:
    import py2app
    from setuptools import setup
except ImportError:
    py2app = None

sys.path.append(os.getcwd())

VERSION_FILE = 'blofeld/version.py'
VERSION_FILEAPP = 'osx/resources/InfoPlist.strings'

def DeleteFiles(name):
    ''' Delete one file or set of files from wild-card spec '''
    for f in glob.glob(name):
        try:
            os.remove(f)
        except:
            print "Cannot remove file %s" % f
            exit(1)

def CheckPath(name):
    if os.name == 'nt':
        sep = ';'
        ext = '.exe'
    else:
        sep = ':'
        ext = ''

    for path in os.environ['PATH'].split(sep):
        full = os.path.join(path, name+ext)
        if os.path.exists(full):
            return name+ext
    print "Sorry, cannot find %s%s in the path" % (name, ext)
    return None


def PatchVersion(name):
    """ Patch in the SVN baseline number, but only when this is
        an unmodified checkout
    """
    try:
        pipe = subprocess.Popen(SvnVersion, shell=True, stdout=subprocess.PIPE).stdout
        svn = pipe.read().strip(' \t\n\r')
        pipe.close()
    except:
        pass

    if not svn:
        print "WARNING: Cannot run %s" % SvnVersion
        svn = 'unknown'

    if not (svn and svn.isdigit()):
        svn = 'unknown'

    try:
        ver = open(VERSION_FILE, 'rb')
        text = ver.read()
        ver.close()
    except:
        print "WARNING: cannot patch " + VERSION_FILE
        return

    regex = re.compile(r'__baseline__\s+=\s+"\w*"')
    text = re.sub(r'__baseline__\s*=\s*"[^"]*"', '__baseline__ = "%s"' % svn, text)
    text = re.sub(r'__version__\s*=\s*"[^"]*"', '__version__ = "%s"' % name, text)
    try:
        ver = open(VERSION_FILE, 'wb')
        ver.write(text)
        ver.close()
    except:
        print "WARNING: cannot patch " + VERSION_FILE

def PairList(src):
    """ Given a list of files and dirnames,
        return a list of (destn-dir, sourcelist) tuples.
        A file returns (path, [name])
        A dir returns for its root and each of its subdirs
            (path, <list-of-file>)
        Always return paths with Unix slashes.
        Skip all SVN elements, .bak .pyc .pyo and *.~*
    """
    lst = []
    for item in src:
        if item.endswith('/'):
            for root, dirs, files in os.walk(item.rstrip('/\\')):
                path = root.replace('\\', '/')
                if path.find('.svn') < 0 and path.find('_svn') < 0 :
                    flist = []
                    for file in files:
                        if not (file.endswith('.bak') or file.endswith('.pyc') or file.endswith('.pyo') or '~' in file):
                            flist.append(os.path.join(root, file).replace('\\','/'))
                    if flist:
                        lst.append((path, flist))
        else:
            path, name = os.path.split(item)
            items = []
            items.append(name)
            lst.append((path, items))
    return lst


def CreateTar(folder, fname, release):
    """ Create tar.gz file for source distro """
    tar = tarfile.open(fname, "w:gz")

    for root, dirs, files in os.walk(folder):
        for _file in files:
            uroot = root.replace('\\','/')
            if (uroot.find('/win') < 0) and (uroot.find('licenses/Python') < 0):
                path = os.path.join(root, _file)
                fpath = path.replace('srcdist\\', release+'/').replace('\\', '/')
                tarinfo = tar.gettarinfo(path, fpath)
                tarinfo.uid = 0
                tarinfo.gid = 0
                if _file in ('Blofeld.py', 'Sample-PostProc.sh'): # One day add: 'setup.py'
                    tarinfo.mode = 0755
                else:
                    tarinfo.mode = 0644
                f= open(path, "rb")
                tar.addfile(tarinfo, f)
                f.close()
    tar.close()

def Dos2Unix(name):
    """ Read file, remove \r and write back """
    base, ext = os.path.splitext(name)
    if ext.lower() not in ('.py', '.txt', '.css', '.js', '.tmpl', '.sh', '.cmd'):
        return

    print name
    try:
        f = open(name, 'rb')
        data = f.read()
        f.close()
    except:
        print "File %s does not exist" % name
        exit(1)
    data = data.replace('\r', '')
    try:
        f = open(name, 'wb')
        f.write(data)
        f.close()
    except:
        print "Cannot write to file %s" % name
        exit(1)


def Unix2Dos(name):
    """ Read file, remove \r, replace \n by \r\n and write back """
    base, ext = os.path.splitext(name)
    if ext.lower() not in ('.py', '.txt', '.css', '.js', '.tmpl', '.sh', '.cmd'):
        return

    print name
    try:
        f = open(name, 'rb')
        data = f.read()
        f.close()
    except:
        print "File %s does not exist" % name
        exit(1)
    data = data.replace('\r', '')
    data = data.replace('\n', '\r\n')
    try:
        f = open(name, 'wb')
        f.write(data)
        f.close()
    except:
        print "Cannot write to file %s" % name
        exit(1)


def rename_file(folder, old, new):
    try:
        oldpath = "%s/%s" % (folder, old)
        newpath = "%s/%s" % (folder, new)
        if os.path.exists(newpath):
            os.remove(newpath)
        os.rename(oldpath, newpath)
    except WindowsError:
        print "Cannot create %s" % newpath
        exit(1)


print sys.argv[0]

#OSX if svnversion not installed install SCPlugin and execute these commands
#sudo cp /Library/Contextual\ Menu\ Items/SCFinderPlugin.plugin/Contents/Resources/SCPluginUIDaemon.app/Contents/lib/lib* /usr/lib
#sudo cp /Library/Contextual\ Menu\ Items/SCFinderPlugin.plugin/Contents/Resources/SCPluginUIDaemon.app/Contents/bin/svnversion /usr/bin

SvnVersion = CheckPath('svnversion')
SvnRevert = CheckPath('svn')
ZipCmd = CheckPath('zip')
UnZipCmd = CheckPath('unzip')
if os.name == 'nt':
    NSIS = CheckPath('makensis')
else:
    NSIS = '-'

# if not (SvnVersion and SvnRevert and ZipCmd and UnZipCmd and NSIS):
if not (ZipCmd and UnZipCmd and NSIS):
    exit(1)

# SvnRevertApp =  SvnRevert + ' revert '
# SvnUpdateApp = SvnRevert + ' update '
# SvnRevert =  SvnRevert + ' revert ' + VERSION_FILE

if len(sys.argv) < 2:
    target = None
else:
    target = sys.argv[1]

if target not in ('source', 'binary', 'installer', 'app'):
    print 'Usage: buildwin32.py binary|source|app'
    exit(1)

# Derive release name from path
base, release = os.path.split(os.getcwd())

prod = 'Blofeld-' + release
Win32ServiceName = 'Blofeld-service.exe'
Win32ConsoleName = 'Blofeld-console.exe'
Win32WindowName  = 'Blofeld.exe'
Win32TempName    = 'Blofeld-windows.exe'

fileIns = prod + '-win32-setup.exe'
fileBin = prod + '-win32-bin.zip'
fileSrc = prod + '-src.tar.gz'
fileDmg = prod + '-osx.dmg'
fileOSr = prod + '-osx-src.tar.gz'
fileImg = prod + '.sparseimage'


# PatchVersion(release)


# List of data elements, directories end with a '/'
data = [ 'interfaces/',
         'views/',
         'AUTHORS',
         'ChangeLog',
         'COPYING',
         'INSTALL',
         'NEWS',
         'README'
       ]

options = dict(
      name = 'Blofeld',
      version = release,
      url = 'http://github.com/daveisadork/Blofeld',
      author = 'Dave Hayes',
      author_email = 'dwhayes@gmail.com',
      #description = 'Blofeld ' + str(blofeld.__version__),
      scripts = ['Blofeld.py'], # One day, add  'setup.py'
      packages = ['blofeld', 'blofeld.library', 'blofeld.utils'],
      platforms = ['posix'],
      license = 'GNU General Public License 2 (GPL2) or later',
      data_files = PairList(data)

)


if target == 'app':
    if not platform.system() == 'Darwin':
        print "Sorry, only works on Apple OSX!"
        os.system(SvnRevert)
        exit(1)

    #Create sparseimage from template
    os.system("unzip blofeld-template.sparseimage.zip")
    os.rename('blofeld-template.sparseimage', fileImg)

    #mount sparseimage
    os.system("hdiutil mount %s" % (fileImg))

    # Unpack cherrypy
    os.system("unzip -o cherrypy.zip")

    import blofeld
    options['description'] = 'Blofeld ' + str(blofeld.__version__)

    #remove prototype and iphone interfaces
    os.system("rm -rf interfaces/prototype>/dev/null")
    os.system("rm -rf interfaces/Concept>/dev/null")
    os.system("rm -rf interfaces/iphone>/dev/null")

    #build Blofeld.py
    sys.argv[1] = 'py2app'

    APP = ['Blofeld.py']
    DATA_FILES = ['interfaces','language',('',glob.glob("osx/resources/*"))]
    NZBFILE = dict(
            CFBundleTypeExtensions = [ "nzb","zip","rar" ],
            CFBundleTypeIconFile = 'nzbfile.icns',
            CFBundleTypeMIMETypes = [ "text/nzb" ],
            CFBundleTypeName = 'NZB File',
            CFBundleTypeRole = 'Viewer',
            LSTypeIsPackage = 0,
            NSPersistentStoreTypeKey = 'Binary',
    )
    OPTIONS = {'argv_emulation': True, 'iconfile': 'osx/resources/blofeldplus.icns','plist': {
       'NSUIElement':1,
       #'CFBundleName':'Blofeld+',
       'CFBundleShortVersionString':release,
       'NSHumanReadableCopyright':'The Blofeld-Team',
       'CFBundleIdentifier':'org.blofeld.team',
       'CFBundleDocumentTypes':[NZBFILE]
       }}

    setup(
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS },
        setup_requires=['py2app'],
    )

    #copy unrar & par2 binary to avoid striping
    os.system("mkdir dist/Blofeld.app/Contents/Resources/osx>/dev/null")
    os.system("mkdir dist/Blofeld.app/Contents/Resources/osx/par2>/dev/null")
    os.system("cp -pR osx/par2/ dist/Blofeld.app/Contents/Resources/osx/par2>/dev/null")
    os.system("mkdir dist/Blofeld.app/Contents/Resources/osx/unrar>/dev/null")
    os.system("cp -pR osx/unrar/ dist/Blofeld.app/Contents/Resources/osx/unrar>/dev/null")
    os.system("chmod +x dist/Blofeld.app/Contents/Resources/update>/dev/null")
    os.system("find dist/Blofeld.app -name .svn | xargs rm -rf")

    #copy builded app to mounted sparseimage
    os.system("cp -r dist/Blofeld.app /Volumes/Blofeld/>/dev/null")

    #cleanup src dir
    os.system("rm -rf dist/>/dev/null")
    os.system("rm -rf build/>/dev/null")
    os.system("find ./ -name *.pyc | xargs rm")
    os.system("rm -rf NSIS_Installer.nsi")
    os.system("rm -rf win/")
    os.system("rm -rf cherrypy*.zip")

    #Create src tar.gz
    os.system("tar -czf %s --exclude \".svn\" --exclude \"sab*.zip\" --exclude \"SAB*.tar.gz\" --exclude \"*.sparseimage\" ./>/dev/null" % (fileOSr) )

    #Copy src tar.gz to mounted sparseimage
    os.system("cp %s /Volumes/Blofeld/Sources/>/dev/null" % (fileOSr))

    #Hide dock icon for the app
    #os.system("defaults write /Volumes/Blofeld/Blofeld.app/Contents/Info LSUIElement 1")

    #Wait for enter from user
    #For manually arrange icon position in mounted Volume...
    #wait = raw_input ("Arrange Icons in DMG and then press Enter to Finalize")

    #Unmount sparseimage
    os.system("hdiutil eject /Volumes/Blofeld/>/dev/null")
    os.system("sleep 5")
    #Convert sparseimage to read only compressed dmg
    os.system("hdiutil convert %s  -format UDBZ -o %s>/dev/null" % (fileImg,fileDmg))
    #Remove sparseimage
    os.system("rm %s>/dev/null" % (fileImg))

    #os.system(SvnRevert)
    # os.system(SvnRevertApp + "NSIS_Installer.nsi")
    # os.system(SvnRevertApp + VERSION_FILEAPP)
    # os.system(SvnRevertApp + VERSION_FILE)
    # os.system(SvnUpdateApp)

elif target in ('binary', 'installer'):
    if not py2exe:
        print "Sorry, only works on Windows!"
        os.system(SvnRevert)
        exit(1)

    import blofeld
    options['description'] = 'Blofeld ' + str(blofeld.__version__)
    
    import pygst
    pygst.require('0.10')
    
    sys.argv[1] = 'py2exe'
    program = [ {'script' : 'Blofeld.py', 'icon_resources' : [(0, "blofeld.ico")] } ]
    options['options'] = {"py2exe":
                              {
                                "bundle_files": 3,
                                "packages": ["gst", "cjson", "jsonlib", "simplejson", "Cheetah.DummyTransaction"],
                                "excludes": ["pywin", "pywin.debugger", "pywin.debugger.dbgcon", "pywin.dialogs",
                                             "pywin.dialogs.list", "Tkconstants", "Tkinter", "tcl"],
                                "optimize": 2,
                                "dll_excludes": [ "kernelbase.dll", "powrprof.dll" ],
                                "compressed": 0
                              }
                         }
    options['zipfile'] = 'lib/blofeld.zip'
    #options['zipfile'] = None


    ############################
    # Generate the console-app
    options['console'] = program
    setup(**options)
    rename_file('dist', Win32WindowName, Win32ConsoleName)


    # Make sure that the root files are DOS format
    for file in options['data_files'][0][1]:
        Unix2Dos("dist/%s" % file)
    # DeleteFiles('dist/Sample-PostProc.sh')
    # DeleteFiles('dist/PKG-INFO')

    # DeleteFiles('*.ini')

    ############################
    # Generate the windowed-app
    options['windows'] = program
    del options['data_files']
    del options['console']
    setup(**options)
    rename_file('dist', Win32WindowName, Win32TempName)


    ############################
    # Generate the service-app
    options['service'] = [{'modules':["Blofeld"], 'cmdline_style':'custom'}]
    del options['windows']
    setup(**options)
    rename_file('dist', Win32WindowName, Win32ServiceName)

    # Give the Windows app its proper name
    rename_file('dist', Win32TempName, Win32WindowName)


    ############################
    if target == 'installer':

        os.system('makensis.exe /v3 /DSAB_PRODUCT=%s /DSAB_FILE=%s NSIS_Installer.nsi' % \
                  (release, fileIns))

        DeleteFiles(fileBin)
        os.rename('dist', prod)
        os.system('zip -9 -r -X %s %s' % (fileBin, prod))
        os.rename(prod, 'dist')

    # os.system(SvnRevert)

else:
    # Prepare Source distribution package.
    # Make sure all source files are Unix format
    import shutil

    root = 'srcdist'
    root = os.path.normpath(os.path.abspath(root))
    if not os.path.exists(root):
        os.mkdir(root)

    # Copy the data files
    for set in options['data_files']:
        dest, src = set
        ndir = root + '/' + dest
        ndir = os.path.normpath(os.path.abspath(ndir))
        if not os.path.exists(ndir):
            os.makedirs(ndir)
        for file in src:
            shutil.copy2(file, ndir)
            Dos2Unix(ndir + '/' + os.path.basename(file))

    # Copy the script files
    for name in options['scripts']:
        file = os.path.normpath(os.path.abspath(name))
        shutil.copy2(file, root)
        base = os.path.basename(file)
        fullname = os.path.normpath(os.path.abspath(root + '/' + base))
        Dos2Unix(fullname)

    # Copy all content of the packages (but skip backups and pre-compiled stuff)
    for unit in options['packages']:
        unitpath = unit.replace('.','/')
        dest = os.path.normpath(os.path.abspath(root + '/' + unitpath))
        if not os.path.exists(dest):
            os.makedirs(dest)
        for name in glob.glob("%s/*.*" % unitpath):
            file = os.path.normpath(os.path.abspath(name))
            front, ext = os.path.splitext(file)
            base = os.path.basename(file)
            fullname = os.path.normpath(os.path.abspath(dest + '/' + base))
            if (ext.lower() not in ('.pyc', '.pyo', '.bak')) and '~' not in ext:
                shutil.copy2(file, dest)
                Dos2Unix(fullname)

    # Install CherryPy
    os.chdir(root)
    os.system("unzip -o ../cherrypy.zip")
    os.chdir('..')

    # Prepare the TAR.GZ pacakge
    CreateTar('srcdist', fileSrc, prod)

    # os.system(SvnRevert)
