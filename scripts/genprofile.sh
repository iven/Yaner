#!/bin/bash
scripts=$(dirname "$0")
basedir=${scripts}/..
python2 -m "profile" -o ${basedir}/profile.out ${basedir}/yaner/Application.py
