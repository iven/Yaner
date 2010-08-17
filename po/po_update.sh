#!/bin/bash
xgettext -k_ -LPython -o yaner.pot ../Yaner/*.py*
xgettext -k_ -j -LGlade -o yaner.pot ../glade/*.ui
msgmerge -o zh_CN.po zh_CN.po yaner.pot
