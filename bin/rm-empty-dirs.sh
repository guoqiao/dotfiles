#!/usr/bin/env bash

root=${1:-.}

find ${root} -type d -empty -print -exec rmdir {} +

