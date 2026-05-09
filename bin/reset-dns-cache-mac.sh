#!/usr/bin/env bash

set -xueo pipefail

sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

