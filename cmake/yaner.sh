#!/bin/sh

BIN="bin/yaner"
if [ -f $BIN ]; then
    exec $BIN "$@"
else
    echo "Yaner not build, read INSTALL first"
fi
