#!/bin/bash

ARCH=`uname -s`
DIR=
RE='^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'
RENR='^[0-9]+$'

if [ $ARCH == "Linux" ]; then
   DIR=`readlink -f "$( dirname "$0" )"`
elif [ $ARCH == "Darwin" ]; then
   CMD="import os, sys; print os.path.realpath(\"$( dirname $0 )\")"
   DIR=`python -c "$CMD"`
fi



if [ $# -eq 0 ]; then
    echo "Starting test mode."
	. $DIR/envHrapi/bin/activate
        python $DIR/api_1_0/pyprox.py
else
	. $DIR/envHrapi/bin/activate
	python $DIR/api_1_0/pyprox.py $1 $2 $3
fi



 
