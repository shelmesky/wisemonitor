#!/bin/sh

. /home/zhaoym/.virtualenvs/tulsa/bin/activate
exec celeryd -l info
