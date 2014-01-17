#!/usr/bin/env python
#!--encoding:utf-8--

from gevent import monkey
monkey.patch_all()

import os
import sys

from api.mongo_api import MongoExecuter
from api.mongo_driver import db_handler
import XenAPI
