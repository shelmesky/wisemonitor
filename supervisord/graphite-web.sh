#!/bin/sh

cd /opt/graphite/webapp/graphite
#exec gunicorn_django -b 0.0.0.0:8002 -w 2
exec gunicorn_django -b 127.0.0.1:8002 -w 2
