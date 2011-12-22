#!/usr/bin/env python

import sys, os
from glob import glob
from os.path import basename, splitext, isdir
from stat import S_IRUSR, S_IWUSR, S_IRGRP, S_IROTH
from distutils.core import setup
from distutils.command.install import install
from distutils.command.install_data import install_data

sys.path.insert(0, '.')
from yaner import __version__, __license__

INSTALLED_FILES = "installed_files"

class Install(install):

    def run(self):
        install.run(self)
        outputs = self.get_outputs()
        length = 0
        if self.root:
            length += len(self.root)
        if self.prefix:
            length += len(self.prefix)
        if length:
            for counter in range(len(outputs)):
                outputs[counter] = outputs[counter][length:]
        with open(INSTALLED_FILES, "w") as install_file:
            install_file.write("\n".join(outputs))

class InstallData(install_data):

    def run(self):
        def chmod_data_file(data_file):
            try:
                os.chmod(data_file, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)
            except:
                self.warn("Could not chmod data file %s" % file)
        install_data.run(self)
        for output in self.get_outputs():
            chmod_data_file(output)

class Uninstall(install):

    def run(self):
        with open(INSTALLED_FILES, "r") as install_file:
            install_files = install_file.readlines()
        prepend = ""
        if self.root:
            prepend += self.root
        if self.prefix:
            prepend += self.prefix
        if len(prepend):
            for counter in range(len(install_files)):
                install_files[counter] = prepend + install_files[counter].rstrip()
        for install_file in install_files:
            print("Uninstalling %s" % install_file)
            try:
                os.unlink(install_file)
            except:
                self.warn("Could not remove file %s" % install_file)

ops = ("install", "build", "sdist", "uninstall", "clean")

if len(sys.argv) < 2 or sys.argv[1] not in ops:
    raise SystemExit("Please specify operation : " + " | ".join(ops))

prefix = None
if len(sys.argv) > 2:
    i = 0
    for o in sys.argv:
        if o.startswith("--prefix"):
            if o == "--prefix":
                if len(sys.argv) >= i:
                    prefix = sys.argv[i + 1]
                sys.argv.remove(prefix)
            elif o.startswith("--prefix=") and len(o[9:]):
                prefix = o[9:]
            sys.argv.remove(o)
            break
        i += 1
if not prefix and "PREFIX" in os.environ:
    prefix = os.environ["PREFIX"]
if not prefix or not len(prefix):
    prefix = "/usr/local"

if sys.argv[1] in ("install", "uninstall") and len(prefix):
    sys.argv += ["--prefix", prefix]

data_files = []
po_buildcmd = "msgfmt -o build/locale/%s/yaner.mo po/%s.po"
for po_file in glob('po/*.po'):
    po_name = splitext(basename(po_file))[0]
    if sys.argv[1] in ('build', 'install'):
        if not isdir("build/locale/" + po_name):
            os.makedirs("build/locale/" + po_name)
        os.system(po_buildcmd % (po_name, po_name))
    data_files.append(("share/locale/%s/LC_MESSAGES" % po_name,
        glob('build/locale/%s/yaner.mo' % po_name)))
config_dir = os.getenv('XDG_CONFIG_DIRS', '/etc/xdg/').split(':')[0]
data_files.append((os.path.join(config_dir, 'yaner'), glob('config/*')))
data_files.append(('share/applications/', ['yaner.desktop']))
data_files.append(('share/glib-2.0/schemas/', ['data/com.kissuki.yaner.gschema.xml']))

setup (
    name             = "yaner",
    version          = __version__,
    description      = "GTK+ interface for aria2 download mananger",
    author           = "Iven Hsu (Xu Lijian)",
    author_email     = "ivenvd@gmail.com",
    url              = "https://github.com/iven/Yaner",
    license          = __license__,
    data_files       = data_files,
    packages         = ["yaner", "yaner.ui", "yaner.utils"],
    package_data     = {'yaner.ui': ['ui.xml']},
    scripts          = ["scripts/yaner"],
    cmdclass         = {"uninstall" : Uninstall,
                        "install" : Install,
                        "install_data" : InstallData},
    )

