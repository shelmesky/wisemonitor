#!/bin/bash


ulimit -SHn 65500

env python run.py --log_file_prefix=wisemonitor.log --logging=info
