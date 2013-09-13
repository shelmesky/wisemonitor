#!/usr/bin/env python
# -- coding: utf-8--
import os
import sys

import __init__
from tornado import ioloop

from common.init import *
from common.api.loader import load_url_handlers
from common.api import XenAPI
from logger import logger
from settings import XEN

global_xenserver_conn = {}


def connect_to_xenserver():
    for host in XEN:
        if host[0] not in global_xenserver_conn:
            try:
                session = XenAPI.Session("http://" + host[0])
                session.login_with_password(host[1], host[2])
                global_xenserver_conn[host[0]] = session
                logger.info("Connect to XenServer: {0} are success.".format(host[0]))
            except Exception, e:
                logger.error(e)
                raise e

connect_to_xenserver()


class iApplication(web.Application):
    def __init__(self):
        settings = {
        "cookie_secret": "27yc1u%9tt3$o^$3uu=6e(=2d7mykjd8@dc*#x0z%vm&0_vdq",
        "debug": True,   # debug mode not compatible with multiprocessing environment.
        "gzip": False,
        'static_path': os.path.join(os.path.dirname(__file__), "static"),
        'js': os.path.join(os.path.dirname(__file__), "js"),
        'css': os.path.join(os.path.dirname(__file__), "css"),
        'img': os.path.join(os.path.dirname(__file__), "img"),
        'template_path': os.path.join(os.path.dirname(__file__), "templates"),
        }
    
        handlers = [
            (r"/", MainHandler),
            (r"/static/(.*)", web.StaticFileHandler, dict(path=settings['static_path'])),
            (r"/css/(.*)", web.StaticFileHandler, dict(path=settings['css'])),
            (r"/js/(.*)", web.StaticFileHandler, dict(path=settings['js'])),
            (r"/img/(.*)", web.StaticFileHandler, dict(path=settings['img'])),
        ]
        
        apps = load_url_handlers()
        handlers.extend(apps)
        web.Application.__init__(self, handlers, **settings)

class MainHandler(WiseHandler):
    def get(self):
        self.render("index.html")
    

if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except Exception:
        port = 1984
    
    app = iApplication()
    app.listen(port, xheaders=True)
    ioloop.IOLoop.instance().start()
