#!/usr/bin/env python

from DistUtilsExtra.auto import setup

from yaner import __version__, __license__

setup(
    name='yaner',
    version=__version__,
    license=__license__,
    author='Iven Hsu (Xu Lijian)',
    author_email='ivenvd@gmail.com',
    url='https://iven.github.com/Yaner',
    platforms='linux',
    package_data={'yaner/ui': ['ui.xml']},
)
