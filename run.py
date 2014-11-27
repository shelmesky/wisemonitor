#!/usr/bin/env python
# -- coding: utf-8--
import os
import sys
import signal
import time
import hashlib
from httplib2 import urlparse
import xmlrpclib
import httplib
import json

import __init__
from tornado import ioloop
from tornado import gen
from tornado import web
from tornado.options import options, define
from tornado.httpclient import AsyncHTTPClient

from common.init import *
from common.api.loader import load_url_handlers
from common.api import XenAPI
from common.decorator import require_login
from common.utils import TimeoutTransport
from common.api import CloudStack as cloudstack_api

from common.api import rabbitmq_client
from common.alert_handlers.nagios import nagios_alert_handler
from common.api.watch_xenserver_events import XenServer_Alerts_Watcher
from common.alert_handlers.xenserver import xenserver_event_handler

from common.api import mongo_api
from common.api import mongo_driver

from common.tree import make_tree


from logger import logger
import settings
from settings import XEN
from settings import MOTOR_DB as DB
from settings import PERF_RANK_SERVER_IP as perf_rank_server
from settings import PERF_RANK_SERVER_PORT as perf_rank_port


global_xenserver_conn = {}


def connect_to_xenserver():
    for host in XEN:
        if host[0] not in global_xenserver_conn:
            try:
                transport = TimeoutTransport()
                session = XenAPI.Session("http://" + host[0], transport)
                try:
                    session.login_with_password(host[1], host[2])
                except XenAPI.Failure as e:
                    master = e.details[1]
                    for i in XEN:
                        if master == i[0]:
                            user = i[1]
                            passwd = i[2]
                    session = XenAPI.Session("http://" + master, transport)
                    session.login_with_password(user, passwd)
                global_xenserver_conn[host[0]] = session
                logger.warn("Connect to XenServer: {0} are success(with timeout).".format(host[0]))
            except Exception, e:
                logger.exception(e)

if settings.XENSERVER_ENABLED: connect_to_xenserver()

global_xenserver_master_conn = {}

def connect_to_xenserver_master():
    for host in XEN:
        if host[0] not in global_xenserver_master_conn:
            try:
                transport = TimeoutTransport()
                session = XenAPI.Session("http://" + host[0], transport)
                session.login_with_password(host[1], host[2])
                global_xenserver_master_conn[host[0]] = session
                logger.warn("Connect to XenServer: {0} are success(with timeout).".format(host[0]))
            except Exception, e:
                logger.exception(e)

if settings.XENSERVER_ENABLED: connect_to_xenserver_master()


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
            (r"^/getdata/$", DataHandler),
            (r"^/save_position/$", PositionHandler),
            (r"^/node_config/$", NodeConfigHandler),
            (r"^/wizcloud_capacity/$", WizCloudCapacityHandler),
            (r"^/perf_rank/([^/]+)/$", PerfRankHandler),
            (r"^/top_alerts/([^/]+)/$", TopAlertsHandler),
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


def get_state(host):
    '''
    取得每个主机的状态和保存的拓扑图的坐标
    如果无坐标，则主机出现在拓扑图的0,0处
    '''
    state = {}
    c = mongo_api.MongoExecuter(mongo_driver.db_handler)
    data = c.query_one("nagios_host_status", {"host": host})
    if data:
        state["status"] = data["return_code"]
        state["X"] = data.get("X", 0)
        state["Y"] = data.get("Y", 0)
        state["node_type"] = data.get("node_type", "host")
        return state
    else:
        state["status"] = 0
        state["X"] = 0
        state["Y"] = 0
        state["node_type"] = "host"
        return state


def get_allhost_state():
    '''
    取得所有主机和主机服务的状态
    '''
    hosts = {}
    c = mongo_api.MongoExecuter(mongo_driver.db_handler)
    data = c.query("nagios_host_status", {})
    for host in data:
        host_name = host["host"]
        hosts[host_name] = {}
        hosts[host_name]["last_update"] = str(host["last_update"])
        hosts[host_name]["output"] = host["output"]
        
        host_service_status = c.query("nagios_service_status", {"host": host_name})
        hosts[host_name]["service_ok"] = 0
        hosts[host_name]["service_warn"] = 0
        hosts[host_name]["service_critical"] = 0
        hosts[host_name]["service_unknow"] = 0
        if host_service_status:
            for host_service in host_service_status:
                if host_service["return_code"] == 0:
                    hosts[host_name]["service_ok"] += 1
                if host_service["return_code"] == 1:
                    hosts[host_name]["service_warn"] += 1
                if host_service["return_code"] == 2:
                    hosts[host_name]["service_critical"] += 1
                if host_service["return_code"] == 3:
                    hosts[host_name]["service_unknow"] += 1
        
        host_info = c.query_one("nagios_hosts", {"host_name": host_name})
        if host_info:
            hosts[host_name]["host_name"] = host_info["host_name"]
            hosts[host_name]["host_alias"] = host_info["host_alias"]
            hosts[host_name]["host_address"] = host_info["host_address"]
            
    return hosts


def process_data(data):
    '''
    根据遍历拓扑树生成的二维结构
    填充每个节点的信息
    '''
    host_dic = {}
    for item in data:
        parents = item["parent_hosts"]
        if len(parents) > 0:
            host_dic[item["host_name"]] = parents[0]["0"]
        else:
            host_dic[item["host_name"]] = None
    iter_tree = make_tree(host_dic)
    
    last_tree = []
    for item in iter_tree:
        temp = {}
        temp['root'] = {}
        temp['root']["node"] = item['root']
        temp['root']["data"] = get_state(item['root'])
        temp['child'] = []
        childs = item['child']
        if len(childs) > 0:
            for child in childs:
                temp_child = {}
                temp_child['node'] = child
                temp_child['parent'] = host_dic.get(child)
                temp_child["data"] = get_state(child)
                temp['child'].append(temp_child)
        last_tree.append(temp)
    return last_tree

def get_cs_conn():
    for cs_host in settings.CLOUD_STACKS:
        host = 'http://' + cs_host['host'] + ':' + cs_host['port']
        client = cloudstack_api.Client(host, cs_host['api_key'], cs_host['secret_key'])
        return client


class PerfRankHandler(web.RequestHandler):
    @gen.coroutine
    @require_login
    def get(self, rank_type):
        http_client = AsyncHTTPClient()
        url = "http://" + perf_rank_server + ":" + str(perf_rank_port) + "/status/"
        url += rank_type
        response = yield http_client.fetch(url)
        if response.code != 200:
            raise response.error
        body = response.body
        if len(body) == 0:
            raise RuntimeError("Empty Body")
        self.set_header("Content-Type", "application/json")
        self.write(body)


class TopAlertsHandler(WiseHandler):
    @require_login
    @gen.coroutine
    def get(self, alert_type):
        top = 10
        alerts = dict()
        alerts['objects'] = []
        if alert_type == "physical":
            cond = {
                "type": "physical_device",
            }
        elif alert_type == "virtual":
            cond = {
                "type": "xenserver"
            }
        else:
            raise RuntimeError("Error alert_type")
        cursor = DB.alerts.find(cond).sort([("created_time", -1)]).limit(top)
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alert.pop("_id")
            alert['created_time'] = str(alert['created_time'])
            alerts['objects'].append(alert)
        self.set_header("Content-Type", "application/json")
        self.write(alerts)


class WizCloudCapacityHandler(web.RequestHandler):
    @gen.coroutine
    @require_login
    def get(self):
        client = get_cs_conn()
        result = yield client.listZones()
        response = result["listzonesresponse"]
        if response['count'] > 0:
            zone_id = response['zone'][0]['id']
        else:
            raise RuntimeError("No Zones in wizcloud")
        capacitys = yield client.listCapacity(zoneid=zone_id, fetchlatest=True)
        
        zone = yield client.listZones(zoneid=zone_id)
        zone_name = zone['listzonesresponse']['zone'][0]['name']
        
        final_data = {
            'capacitys': capacitys,
            'zone_id': zone_id,
            'zone_name': zone_name,
        }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(final_data))
    
    
class NodeConfigHandler(web.RequestHandler):
    @require_login
    def post(self):
        data = json.loads(self.request.body)
        node_config = data["data"]
        node_name = node_config.get("node_name", None)
        node_type = node_config.get("node_type", None)
        if node_name and node_type:
            c = mongo_api.MongoExecuter(mongo_driver.db_handler)
            c.update("nagios_host_status", {"host": node_name}, {"node_type": node_type})
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"return_code" :0}))
        else:
            self.send_error(500)


class PositionHandler(web.RequestHandler):
    @require_login
    def post(self):
        '''
        保存所有节点在拓扑图中的坐标位置
        并在settings集合中记录一个'top_has_saved'的标志
        作为判断所有节点是否保存坐标的依据
        '''
        c = mongo_api.MongoExecuter(mongo_driver.db_handler)
        data = json.loads(self.request.body)
        node_position = data["data"]
        for host_name, position in node_position.items():
            c.update("nagios_host_status", {"host": host_name}, {"X": position["X"], "Y": position["Y"]})
            
        if not c.query_one("settings", {"topo_has_saved": 1}):
            c.insert("settings", {"topo_has_saved": 1})
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"return_code" :0}))


class DataHandler(web.RequestHandler):
    @require_login
    def get(self):
        '''
        返回前序遍历拓扑图生成的各子树的有序列表
        并判断拓扑图中所有节点的坐标是否保存过
        如果保存过前端使用保存的坐标显示节点
        否则节点的位置自动显示
        '''
        c = mongo_api.MongoExecuter(mongo_driver.db_handler)
        data = c.query("nagios_hosts", {})
        result = process_data(data)
        
        data = c.query_one("settings", {})
        top_has_saved = 0
        if data:
            top_has_saved = 1
        
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"data": result,
                               "all_host_data": get_allhost_state(),
                               "topo_has_saved": top_has_saved}))


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
    
    options.parse_command_line()
    
    # Receive alerts from RabbitMQ that send by Nagios
    if settings.NAGIOS_HANDLE_ENABLED:
        mq_host = settings.MQ_HOST
        mq_username = settings.MQ_USERNAME
        mq_password =  settings.MQ_PASSWORD
        mq_virtual_host = settings.MQ_VIRTUAL_HOST
        
        rabbitmq_client.NagiosReceiver(mq_host, mq_username, mq_password,
                       mq_virtual_host, callback=nagios_alert_handler)
        logger.info("Start Nagios Watcher OK.")
    
    # Receive alerts from XenServer
    # Connect to XenServer without timeout
    if settings.XENSERVER_HANDLE_ENABLED:
        for host in XEN:
            try:
                session = XenAPI.Session("http://" + host[0])
                session.login_with_password(host[1], host[2])
                logger.warn("Connect to XenServer: {0} are success.".format(host[0]))
            except Exception, e:
                logger.exception(e)
            else:
                t = XenServer_Alerts_Watcher(host[0], session, xenserver_event_handler)
                t.start()
                logger.warn("Start XenServer event watcher for %s." % host[0])
        logger.info("Start XenServer Watcher OK.")
    
    app = iApplication()
    app.listen(port, xheaders=True)
    logger.info("Start server OK.")
    
    try:
        ioloop = ioloop.IOLoop.instance()
        ioloop.start()
    except (KeyboardInterrupt, SystemExit):
        ioloop.close()

