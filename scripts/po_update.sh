#!/bin/bash

scripts=$(dirname "$0")
base=${scripts}/..
po=${base}/po

xgettext -k_ -LPython -o ${po}/yaner.pot ${base}/Yaner/*.py*
xgettext -k_ -j -LGlade -o ${po}/yaner.pot ${base}/glade/*.ui
msgmerge -o ${po}/zh_CN.po ${po}/zh_CN.po ${po}/yaner.pot
