#!/bin/bash

scripts=$(dirname "$0")
base=${scripts}/..
po=${base}/po
yaner=${base}/yaner

xgettext -k_ -LPython -o ${po}/yaner.pot ${yaner}/*.py ${yaner}/ui/*.py ${yaner}/utils/*.py
xgettext -k_ -j -LGlade -o ${po}/yaner.pot ${yaner}/ui/*.ui
msgmerge -o ${po}/zh_CN.po ${po}/zh_CN.po ${po}/yaner.pot
