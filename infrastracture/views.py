#! --encoding: utf-8--
import os
import sys
import json
import re
import bson

from tornado import web 
from tornado import gen
from settings import MOTOR_DB as DB
from settings import NAGIOS_CHECK_SNMP_INT_COMMAND

import motor

from common.init import WiseHandler
from common.utils import get_four_hours_ago, get_one_day_ago
from common.utils import get_one_week_ago, get_one_year_ago
from common.utils import get_chart_colors
from common.decorator import require_login
from fields_in_chinese import convert_field
from common.api import nagios
#from common.api import snmp

from utils import physical_perdata_to_excel
from logger import logger


class Infra_Server_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        keyword = self.get_argument("keyword", "").strip()
        limit = self.get_argument("limit", "")
        page = self.get_argument("page", "")
        
        if page:
            try:
                page = int(page)
            except:
                page = 0
        else:
            page = 0
            
        if page == -1:
            page = 0
        
        if limit:
            try:
                limit = int(limit)
            except:
                limit = 5
        else:
            limit = 5
        
        host_cond = None
        host_status_cond = None
        
        origin_keyword = None
        if keyword:
            origin_keyword = keyword
            if not keyword.startswith("@"):
                host_cond = {
                    "$or": [
                        {"host_name": re.compile(".*%s.*" % keyword)},
                        {"host_address": re.compile(".*%s.*" % keyword)},
                    ]
                }
            else:
                keyword = keyword[1:]
                if keyword == "warn":
                    host_status_cond = {
                        "return_code": 1
                    }
                elif keyword == "critical":
                    host_status_cond = {
                        "return_code": 2
                    }
                elif keyword == "unknow":
                    host_status_cond = {
                        "return_code": 3
                    }
        
        cursor = DB.nagios_hosts.find(host_cond)
        
        ret = dict()
        ret['objects'] = list()
        i = 1
        
        while(yield cursor.fetch_next):
            host = cursor.next_object()
            temp = dict()
            host_object_id = host['object_id']
            if host_status_cond:
                host_status_cond["object_id"] = host['object_id']
                cursor_one = DB.nagios_host_status.find(host_status_cond)
            else:
                cursor_one = DB.nagios_host_status.find({"object_id": host['object_id']})
            yield cursor_one.fetch_next
            host_status = cursor_one.next_object()
            if host_status:
                temp['id'] = i
                temp['_id'] = str(host_object_id)
                temp['host_name'] = host['host_name']
                temp['host_address'] = host['host_address']
                temp['notification_period'] = host['host_notification_period']
                temp['state'] = host_status['state'] if host_status['state'] else 0
                temp['return_code'] = host_status['return_code'] if host_status['return_code'] else 0
                temp['last_update'] = host_status['last_update']
                temp['output'] = host_status['output']
                i += 1
                ret['objects'].append(temp)
            
        ret['objects'].sort(key=lambda x: x['_id'])
        
        # 因为使用了多次查询, 不能按照传统思路使用skip和limit函数
        # 所以这里直接从list中获取slice
        server_list_origin = ret['objects']
        server_list = server_list_origin[page*limit : (page*limit) + limit]
        
        # server_list_origin是最终查询到的记录集
        # 而不是上面查询主机的结果
        record_count = len(server_list_origin)
        
        # 一次最多显示几页
        max_per_page = 3
        
        max_pages = record_count / limit
        if record_count % limit != 0:
            max_pages += 1
        
        # 存储当前显示的页数
        page_elements = []
        start = 0
        end = 0
        
        # 如果总页数大于10，则默认显示到第10页结束
        # 否则直接显示总页数
        if max_pages >= max_per_page:
            end = max_per_page
        else:
            end = max_pages
        
        if page >= max_per_page:
            current_ten_page = page / max_per_page
            start = current_ten_page * max_per_page
            end = start + max_per_page
            
            if end > max_pages:
                remain_page_nums = max_pages % max_per_page
                if remain_page_nums > 0:
                    end = start + remain_page_nums
        
        for i in range(start, end):
            page_elements.append(i)
        
        current_page = page
        prev_page = current_page - 1
        next_page = current_page + 1
        # 分页结束
        
        self.render("infrastracture/server.html",
                    server_list=server_list,
                    limit=limit, keyword=origin_keyword,
                    real_pages=page_elements,
                    max_pages=max_pages-1,
                    min_pages=0,
                    current_page=current_page,
                    prev_page=prev_page,
                    next_page=next_page)


class Infra_Server_Services_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self, ip):
        keyword = self.get_argument("keyword", "").strip()
        limit = self.get_argument("limit", "")
        page = self.get_argument("page", "")
        
        if page:
            try:
                page = int(page)
            except:
                page = 0
        else:
            page = 0
            
        if page == -1:
            page = 0
        
        if limit:
            try:
                limit = int(limit)
            except:
                limit = 5
        else:
            limit = 5
        
        cond = None
        origin_keyword = None
        if keyword:
            origin_keyword = keyword
            if not keyword.startswith("@"):
                cond = {
                    "$or": [
                        {"output": re.compile(".*%s.*" % keyword)},
                        {"service": re.compile(".*%s.*" % keyword)},
                    ]
                }
            else:
                keyword = keyword[1:]
                if keyword == "warn":
                    cond = {
                        "return_code": 1
                    }
                elif keyword == "critical":
                    cond = {
                        "return_code": 2
                    }
                elif keyword == "unknow":
                    cond = {
                        "return_code": 3
                    }
        
        cursor = DB.nagios_hosts.find({"host_name": ip})
        yield cursor.fetch_next
        host = cursor.next_object()
        
        if cond:
            cond["host"] = host["host_name"]
            cursor_one = DB.nagios_service_status.find(cond)
        else:
            cursor_one = DB.nagios_service_status.find({"host": host["host_name"]})
            
        # 开始分页
        record_count = yield motor.Op(cursor_one.count)
        cursor_one = cursor_one.skip(page * limit).limit(limit)
        
        # 一次最多显示几页
        max_per_page = 10
        
        max_pages = record_count / limit
        if record_count % limit != 0:
            max_pages += 1
        
        # 存储当前显示的页数
        page_elements = []
        start = 0
        end = 0
        
        # 如果总页数大于10，则默认显示到第10页结束
        # 否则直接显示总页数
        if max_pages >= max_per_page:
            end = max_per_page
        else:
            end = max_pages
        
        if page >= max_per_page:
            current_ten_page = page / max_per_page
            start = current_ten_page * max_per_page
            end = start + max_per_page
            
            if end > max_pages:
                remain_page_nums = max_pages % max_per_page
                if remain_page_nums > 0:
                    end = start + remain_page_nums
        
        for i in range(start, end):
            page_elements.append(i)
        
        current_page = page
        prev_page = current_page - 1
        next_page = current_page + 1
        # 分页结束
            
        ret = dict()
        ret['objects'] = list()
        i = 1
        while(yield cursor_one.fetch_next):
            service = cursor_one.next_object()
            temp = dict()
            temp['_id'] = str(service['object_id'])
            temp['id'] = i
            temp['host_name'] = service['host']
            temp['service_name'] = service['service']
            temp['state'] = service['state']
            temp['return_code'] = service['return_code']
            temp['output'] = service['output']
            temp['last_update'] = service['last_update']
            if service['perfdata'] != "":
                temp['has_perfdata'] = True
            else:
                temp['has_perfdata'] = False
            i += 1
            ret['objects'].append(temp)
            
        ret['objects'].sort(key=lambda x: x['_id'])
        self.render("infrastracture/services.html",
                    services_list=ret['objects'], host_ip=ip,
                    limit=limit, keyword=origin_keyword,
                    real_pages=page_elements,
                    max_pages=max_pages-1,
                    min_pages=0,
                    current_page=current_page,
                    prev_page=prev_page,
                    next_page=next_page)


@gen.coroutine
def parse_perfdata(cursor, frequency=1, callback=None):
    """
    根据frequency(频率)计算平均值
    每段数据的时间点，取每段的第一条数据
    """
    fields_data = {}
    
    # 获取性能数据的字段
    fields = []
    while(yield cursor.fetch_next):
        record = cursor.next_object()
        perf_data = record['perf_data']
        for item in perf_data:
           field = item['field']
           if "/" in field:
               field = field.replace("/", "_")
           if "'" in field:
               field = field.replace("'", "")
           fields.append(field)
        break
    
    cursor.rewind()
    
    #根据预先定义的颜色值，设置每个数据字段的颜色
    colors = get_chart_colors()
    
    # 预先填充字段名
    for field in fields:
        if "/" in field:
            field = field.replace("/", "_")
        if "'" in field:
            field = field.replace("'", "")
        fields_data[str(field)] = {}
        fields_data[str(field)]['data'] = []
        fields_data[str(field)]['color'] = colors.pop()
    
    final_data = []
    while(yield cursor.fetch_next):
        record = cursor.next_object()
        final_data.append(record)
        
    data_length = len(final_data)
    
    for i in xrange(0, data_length, frequency):
        start = i
        if start >0 and frequency>1:
            start = start - 1
        end = i + frequency
        
        temp_data = {}
        for f in fields:
            temp_data[str(f)] = 0
        
        temp_timestamp = int(final_data[start]['timestamp'] * 1000)
        
        for record in final_data[start:end]:
            perf_data = record['perf_data']
            for item in perf_data:
                field = str(item['field'])
                if "/" in field:
                    field = field.replace("/", "_")
                if "'" in field:
                    field = field.replace("'", "")
                data = item['data'][0]
                
                
                # 如果记录中已经存在字段的'别名'
                if "field_alias" in item:
                    fields_data[field]['field_alias'] = item['field_alias']
                        
                # 如果数据的'单位'已经存在与记录中
                if "unit" in item:
                    unit = item['unit']
                else:
                    unit = re.match(r".*\d(.*)", data).groups()[0]
                fields_data[field]['unit'] = str(unit)
                
                # 替换数据中的'单位'字符串为空格
                temp_data[field] += float(data.replace(unit, ""))
            
        for k,v in temp_data.items():
            value = "%.2f" % (v/frequency)
            fields_data[k]['data'].append([temp_timestamp, float(value)])
        
    callback(fields_data)


class Infra_Server_Chart_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self, host, chart_type):
        self.host = host
        self.chart_type = chart_type
        
        collection_perfdata = "nagios_host_perfdata"
        collection_hosts = "nagios_hosts"
        
        if not chart_type or not host:
            self.send_error(404)
        
        self.host = host
        self.chart_type = chart_type
        
        if chart_type == "4h":
            ago = get_four_hours_ago()
            frequency = 1
        elif chart_type == "24h":
            ago = get_one_day_ago()
            frequency = 1
        elif chart_type == "1w":
            ago = get_one_week_ago()
            frequency = 12
        elif chart_type == "1y":
            ago = get_one_year_ago()
        else:
            ago = None
        
        if chart_type != "1y":
            if ago:
                cursor = DB.nagios_hosts.find({"host_address": host})
                yield cursor.fetch_next
                result = cursor.next_object()
                
                object_id = result['object_id']
                cursor = DB.nagios_host_perfdata.find({"object_id": object_id, "timestamp": {"$gte": ago}})
            
                yield parse_perfdata(cursor, frequency, self.on_parse_finished)
            else:
                self.send_error(500)
        else:
            pass
        
    def on_parse_finished(self, data):
        download_excel = self.get_argument("excel", None)
        if download_excel == "yes":
            file_name = self.host + "-" + self.chart_type + ".xls"
            excel_data = physical_perdata_to_excel(data)
            user_agent = self.request.headers['User-Agent']
            if "MSIE" in user_agent:
                self.add_header("Content-Type", "application/vnd.ms-excel")
            else:
                self.add_header("Content-Type", "application/ms-excel")
            self.add_header("Content-Disposition", "attachment; filename=%s" % file_name)
            self.write(excel_data)
        else:
            self.render("infrastracture/server_chart.html", host=self.host,
                        chart_type=self.chart_type, data=data, convert_field=convert_field)
    
    
class Infra_Service_Chart_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self, host, service, chart_type):
        self.host = host
        self.chart_type = chart_type
        
        if not chart_type or not host or not service:
            self.send_error(404)
        
        self.host_address = host
        self.chart_type = chart_type
        self.service_object_id = bson.ObjectId(service)
        
        cursor = DB.nagios_services.find({"object_id": self.service_object_id})
        yield cursor.fetch_next
        self.service_name = cursor.next_object()['service_description']
        
        if chart_type == "4h":
            ago = get_four_hours_ago()
            frequency = 1
        elif chart_type == "24h":
            ago = get_one_day_ago()
            frequency = 1
        elif chart_type == "1w":
            ago = get_one_week_ago()
            frequency = 12
        elif chart_type == "1y":
            ago = get_one_year_ago()
        else:
            ago = None
        
        if chart_type != "1y":
            if ago:
                cursor = DB.nagios_service_perfdata.find({"object_id": self.service_object_id, "timestamp": {"$gte": ago}})
            
                yield parse_perfdata(cursor, frequency, self.on_parse_finished)
            else:
                self.send_error(500)
        else:
            pass
        
    def on_parse_finished(self, data):
        download_excel = self.get_argument("excel", None)
        if download_excel == "yes":
            file_name = self.host + "-" + self.service_name + "-" + self.chart_type + ".xls"
            excel_data = physical_perdata_to_excel(data)
            user_agent = self.request.headers['User-Agent']
            if "MSIE" in user_agent:
                self.add_header("Content-Type", "application/vnd.ms-excel")
            else:
                self.add_header("Content-Type", "application/ms-excel")
            self.add_header("Content-Disposition", "attachment; filename=%s" % file_name)
            self.write(excel_data)
        else:
            self.render("infrastracture/service_chart.html", host_address=self.host_address,
                        service_name=self.service_name, chart_type=self.chart_type,
                        service_object_id=self.service_object_id, data=data, convert_field=convert_field)


class Infra_AddServer_Handler(WiseHandler):
    @require_login
    def get(self):
        return self.render("infrastracture/add_server.html", updated=None)
    
    @require_login
    def post(self):
        host_name = self.get_argument("host_name", "").strip()
        alias = self.get_argument("alias", "").strip()
        address = self.get_argument("address", "").strip()
        use = self.get_argument("use", "").strip()
        
        _snmp_supported = self.get_argument("snmp_supported", "").strip()
        _snmp_community = self.get_argument("snmp_community", "").strip()
        if _snmp_supported == '1' and not _snmp_community:
            return self.render("infrastracture/add_server.html",
                               updated="failed", new_server=host_name)
        
        kwargs = {
            '_snmp_supported': _snmp_supported
        }
        if _snmp_community:
            kwargs['_snmp_community'] = _snmp_community
        
        if host_name and alias and address and use:
            result, err = nagios.add_host(
                host_name = host_name,
                alias = alias,
                address = address,
                use = use,
                **kwargs
            )
            if result != True:
                try:
                    raise err
                except Exception, e:
                    logger.exception(e)
                return self.render("infrastracture/add_server.html",
                                   updated="failed", new_server=host_name)
            
            result, err = nagios.restart_nagios_process()
            if result != True:
                try:
                    raise err
                except Exception, e:
                    logger.exception(e)
                return self.render("infrastracture/add_server.html",
                                   updated="failed", new_server=host_name)
            
            return self.render("infrastracture/add_server.html",
                               updated="ok", new_server=host_name)
        else:
            return self.render("infrastracture/add_server.html",
                               updated="failed", new_server=host_name)


class Infra_AddDataTrafficService_Handler(WiseHandler):
    @require_login
    def get(self, host_ip):
        all_interface = None
        snmp_supported, community = self.check_snmp_supported(host_ip)
        if snmp_supported:
            all_interface = self.get_all_interface(host_ip, community)
        return self.render("infrastracture/add_service_data_traffic.html",
                           error=None, host_ip=host_ip,
                           all_interface=all_interface,
                           snmp_supported=snmp_supported)
    
    @require_login
    def post(self, host_ip):
        error = None
        use = self.get_argument("use", "").strip()
        interface_index = self.get_argument("interface_index", "").strip()
        in_warn = self.get_argument("in_warn", "").strip()
        out_warn = self.get_argument("out_warn", "").strip()
        in_crit = self.get_argument("in_crit", "").strip()
        out_crit = self.get_argument("out_crit", "").strip()
        
        snmp_supported, community = nagios.check_if_snmp_supported(host_ip)
        if not snmp_supported:
            error = "failed"
            logger.error("host %s does not support SNMP!" % host_ip)
            all_interface = self.get_all_interface(host_ip, community)
            return self.render("infrastracture/add_service_data_traffic.html",
                               error=error, host_ip=host_ip,
                               snmp_supported=False,
                               all_interface=all_interface)
            
        try:
            speed, status, name, index = snmp.get_int_status(host_ip, community,
                                                             interface_index=interface_index)
        except Exception, e:
            logger.exception(e)
            error = "failed"
            return self.render("infrastracture/add_service_data_traffic.html",
                               error=None, host_ip=host_ip)
        else:
            if speed or status:
                address = host_ip
                service_description = name
                use = use
                
                snmp_int_command = NAGIOS_CHECK_SNMP_INT_COMMAND
                interface_name = name
                
                in_warn_speed = (speed/1000) * (int(in_warn)/100.0)
                out_warn_speed = (speed/1000) * (int(out_warn)/100.0)
                in_crit_speed = (speed/1000) * (int(in_crit)/100.0)
                out_crit_speed = (speed/1000) * (int(out_crit)/100.0)
                
                check_command = "%s!%s!'^%s$'" % (snmp_int_command, community, interface_name)
                check_command_warn_and_crit = "!%s!%s!%s!%s!%s" % (
                    in_warn_speed,
                    out_warn_speed,
                    in_crit_speed,
                    out_crit_speed,
                    60,
                )
                check_command += check_command_warn_and_crit
                
                ret, err = nagios.add_service(
                    address=address,
                    service_description = service_description,
                    use=use,
                    check_command=check_command,
                    normal_check_interval=1
                )
                if ret != True:
                    try:
                        raise err
                    except Exception, e:
                        logger.exception(e)
                        error = "failed"
                        all_interface = self.get_all_interface(host_ip, community)
                        return self.render("infrastracture/add_service_data_traffic.html",
                                   error="failed", host_ip=host_ip,
                                   snmp_supported=snmp_supported,
                                   all_interface=all_interface,
                                   service_name=service_description)
                
                all_interface = self.get_all_interface(host_ip, community)
                return self.render("infrastracture/add_service_data_traffic.html",
                               error="ok", host_ip=host_ip,
                               all_interface=all_interface,
                               snmp_supported=snmp_supported,
                               service_name=service_description)


    def check_snmp_supported(self, host_ip):
        """
        检查nagios配置文件中，主机是否支持SNMP
        如果支持返回它的SNMP Community
        """
        snmp_supported, community = nagios.check_if_snmp_supported(host_ip)
        self.community = community
        return snmp_supported, community

    def get_all_interface(self, host_ip, community):
        """
        获取某台主机上所有的端口
        """
        all_interface = snmp.get_all_interface(host_ip, community)
        return all_interface


class Infra_AddCommonService_Handler(WiseHandler):
    @require_login
    def get(self, host_ip):
        return self.render("infrastracture/add_service_common.html", updated=None)


class Infra_SNMP_Handler(WiseHandler):
    @require_login
    def post(self, host_ip):
        """
        根据端口index，查询端口的速度和状态
        """
        snmp_supported, community = nagios.check_if_snmp_supported(host_ip)
        if snmp_supported:
            interface_index = self.get_argument("index", "").strip()
            interface_name = self.get_argument("name", "").strip()
            interface_name = interface_name.split(" ")[0]
            try:
                ret = snmp.get_int_status(host_ip, community,
                                                                        interface_index=int(interface_index))
                if ret != None:
                    interface_speed, interface_status, _, _ = ret
                else:
                    msg = {
                        "interface_name": interface_name,
                        "speed": 0,
                        "status": 2 
                    }
                    self.write(json.dumps(msg))
                    return
            except Exception, e:
                logger.error("Get interface %s status failed!" % interface_name)
                msg = {
                    "interface_name": interface_name,
                    "speed": 0,
                    "status": 2 
                }
                self.write(json.dumps(msg))
            else:
                if interface_speed or interface_status:
                    msg = {
                        "interface_name": interface_name,
                        "speed": int(interface_speed),
                        "status": int(interface_status)
                    }
                    self.write(json.dumps(msg))

