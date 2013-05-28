#!/bin/sh

cd /opt/graphite/bin

# use debug to let carbon run foreground
exec ./carbon-cache.py --debug start
