#!/usr/bin/env python
# -- coding: utf-8--
import os
import sys
import signal
import time
import hashlib
from httplib2 import urlparse

import __init__
from tornado import ioloop
from tornado import gen
from tornado import web

from common.init import *
from common.api.loader import load_url_handlers
from common.api import XenAPI
from common.decorator import require_login

from common.api import rabbitmq_client
from common.alert_handlers.nagios import nagios_alert_handler
from common.api.watch_xenserver_events import XenServer_Alerts_Watcher
from common.alert_handlers.xenserver import xenserver_event_handler

from logger import logger
import settings
from settings import XEN
from settings import MOTOR_DB as DB

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

if settings.XENSERVER_ENABLED: connect_to_xenserver()


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
            (r"^/$", MainHandler),
            (r"^/login/$", LoginHandler),
            (r"^/logout/$", LogoutHandler),
            (r"^/static/(.*)", web.StaticFileHandler, dict(path=settings['static_path'])),
            (r"^/css/(.*)", web.StaticFileHandler, dict(path=settings['css'])),
            (r"^/js/(.*)", web.StaticFileHandler, dict(path=settings['js'])),
            (r"^/img/(.*)", web.StaticFileHandler, dict(path=settings['img'])),
        ]
        
        apps = load_url_handlers()
        handlers.extend(apps)
        # custom http error handler
        handlers.append((r"/.*", PageNotFound))
        web.Application.__init__(self, handlers, **settings)


class MainHandler(WiseHandler):
    @require_login
    def get(self):
        self.render("index.html")


class LoginHandler(WiseHandler):
    def get(self):
        if self.get_secure_cookie("wisemonitor_user"):
            self.redirect("/")
        self.render("login.html", error=None)
    
    @web.asynchronous
    @gen.coroutine
    def post(self):
        next_url = None
        referer = self.request.headers['Referer']
        parsed_referer = urlparse.parse_qs(referer)
        if parsed_referer:
            next_url = parsed_referer.values()[0][0]
        
        error = None
        username = self.get_argument("username", "").strip()
        password = self.get_argument("password", "").strip()
        if username and password:
            cursor = DB.users.find({"username": username})
            yield cursor.fetch_next
            user = cursor.next_object()
            if not user:
                error = -1
                self.render("login.html", error=error)
                return
            password_digest = hashlib.md5(password).hexdigest()
            if user['password'] == password_digest:
                self.set_secure_cookie("wisemonitor_user", username)
                if next_url:
                    self.redirect(next_url)
                else:
                    self.redirect("/")
            else:
                error = 1
                self.render("login.html", error=error)
        else:
            error = 2
            self.render("login.html", error=error)


class LogoutHandler(WiseHandler):
    def get(self):
        self.set_secure_cookie("wisemonitor_user", "")
        self.redirect("/login/")


class Watcher:   
    def __init__(self):   
        self.child = os.fork()   
        if self.child == 0:   
            return  
        else:   
            self.watch()
            
    def watch(self):   
        try:   
            os.wait()   
        except (KeyboardInterrupt, SystemExit):   
            # I put the capital B in KeyBoardInterrupt so I can   
            # tell when the Watcher gets the SIGINT
            print "Server exit at %s." % time.ctime()
            self.kill()   
        sys.exit()   
  
    def kill(self):   
        try:   
            os.kill(self.child, signal.SIGKILL)   
        except OSError: pass 
    

if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
    except Exception:
        port = 1984
    
    Watcher()
    
    # Receive alerts from RabbitMQ that send by Nagios
    if settings.NAGIOS_HANDLE_ENABLED:
        mq_host = settings.MQ_HOST
        mq_username = settings.MQ_USERNAME
        mq_password =  settings.MQ_PASSWORD
        mq_virtual_host = settings.MQ_VIRTUAL_HOST
        
        rabbitmq_client.NagiosReceiver(mq_host, mq_username, mq_password,
                       mq_virtual_host, callback=nagios_alert_handler)
    
    # Receive alerts from XenServer
    if settings.XENSERVER_HANDLE_ENABLED:
        for host, session in global_xenserver_conn.items():
            t = XenServer_Alerts_Watcher(host, session, xenserver_event_handler)
            t.start()
    
    app = iApplication()
    app.listen(port, xheaders=True)
    
    try:
        ioloop.IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
        ioloop.IOLoop.instance().close()

