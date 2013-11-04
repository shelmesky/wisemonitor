#!/usr/bin/env python
#!--encoding:utf-8--

import base64
import hashlib
import hmac
import json
import urllib

from tornado import gen
from tornado import web
from tornado import ioloop
from tornado import escape
from tornado.httpclient import AsyncHTTPClient


def capacity_type_string(type_id):
    return {                                                                                
        0: 'memory',  # bytes
        1: 'cpu',  # MHz
        2: 'primary_storage_used',  # bytes
        3: 'primary_storage_allocated',  # bytes
        4: 'public_ips',
        5: 'private_ips',
        6: 'secondary_storage',  # bytes
    }.get(type_id, 'unknown')


class Client(object):
    def __init__(self, base_url, api_key, secret_key):
        self.base_url = base_url
        self.api_key = api_key
        self.secret_key = secret_key
        self._page_size = None
    
    def _sign(self, url):
        base_url, query_string = url.split('?')
        msg = '&'.join(sorted(x.lower() for x in query_string.split('&')))
        
        signature = base64.b64encode(hmac.new(
            self.secret_key, msg=msg, digestmod=hashlib.sha1).digest())
        
        return "%s?%s&signature=%s" % (
            base_url, query_string, urllib.quote(signature))
    
    @gen.coroutine
    def _request_single(self, command, **kwargs):
        _http_client = AsyncHTTPClient()
        
        params = kwargs
        params['command'] = command
        params['apiKey'] = self.api_key
        params['response'] = 'json'
        
        url = self._sign("%s/client/api?%s" % (
            self.base_url, urllib.urlencode(params)))
        
        resp = yield _http_client.fetch(url)
        body = escape.json_decode(resp.body)
        raise gen.Return(body)
    
    def _process_page_size(self, result):
        configs_response = result.get('listconfigurationsresponse', {})
        configs = configs_response.get('configuration', [])
        if len(configs) == 1 and configs[0]['name'] == 'default.page.size':
            return int(configs[0]['value'])

    @gen.coroutine
    def _get_page_size(self):
        if self._page_size is None:
            _result = yield self._request_single('listConfigurations', name='default.page.size')
            self._page_size = self._process_page_size(_result)
    
    @gen.coroutine
    def _request(self, command, **kwargs):
        #yield self._get_page_size()
        result = yield self._request_single(command, **kwargs)
        raise gen.Return(result)
    
    @gen.coroutine
    def listHosts(self, **kwargs):
        result = yield self._request('listHosts', **kwargs)
        raise gen.Return(result)
    
    @gen.coroutine
    def listConfigurations(self, **kwargs):
        result = yield self._request('listConfigurations', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listDomains(self, **kwargs):
        result = yield self._request('listDomains', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listDomainChildren(self, **kwargs):
        result = self._request('listDomainChildren', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listZones(self, **kwargs):
        result = yield self._request('listZones', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listPods(self, **kwargs):
        result = yield self._request('listPods', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listClusters(self, **kwargs):
        result = yield self._request('listClusters', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listSystemVms(self, **kwargs):
        result = yield self._request('listSystemVms', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listRouters(self, **kwargs):
        result = yield self._request('listRouters', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listVirtualMachines(self, **kwargs):
        result = yield self._request('listVirtualMachines', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listCapacity(self, **kwargs):
        result = yield self._request('listCapacity', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listAlerts(self, **kwargs):
        result = yield self._request('listAlerts', **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def listEvents(self, **kwargs):
        result = yield self._request('listEvents', **kwargs)
        raise gen.Return(result)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, "../../")

    import  settings
    cs_host = settings.CLOUD_STACKS[0]
    url = "http://" + cs_host['host'] + ":" + cs_host['port']
    api_key = cs_host['api_key']
    secret_key = cs_host['secret_key']

    
    class Main(web.RequestHandler):
        @web.asynchronous
        @gen.coroutine
        def get(self):
            from pprint import pprint
            client = Client(url, api_key, secret_key)
            result = yield client.listZones()
            pprint(result)
            
            print "#" * 100
            result = yield client.listPods()
            pprint(result)
            
            print "#" * 100
            result = yield client.listClusters()
            pprint(result)
            
            print "#" * 100
            result = yield client.listHosts()
            pprint(result)

            print "#" * 100
            result = yield client.listVirtualMachines()
            pprint(result)
            
            print "#" * 100
            result = yield client.listSystemVms()
            pprint(result)

            print "#" * 100
            result = yield client.listAlerts()
            pprint(result)

    
    app = web.Application([
        (u"/", Main)
        ])
    
    app.listen(8888)
    ioloop.IOLoop.instance().start()
