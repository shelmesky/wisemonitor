#!/bin/bash

nohup ./start.sh &
nohup ./api_server.py &

cd bin/VNCProxy
nohup ./start.sh &

cd ../PerfGetter
nohup python ./server.py &
