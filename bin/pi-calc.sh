#!/usr/bin/env bash

SCALE=${1:-5000}
echo "calc pi to $SCALE digits ..."
echo "scale=$SCALE; 4*a(1)" | /usr/bin/time -p bc -l

