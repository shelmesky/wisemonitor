#!/usr/bin/python
from gevent import monkey
monkey.patch_all()

from xml.dom import minidom
from xml.parsers.expat import ExpatError
import time
import pprint
import json


# Per VM dictionary (used by RRDUpdates to look up column numbers by variable names)
class VMReport(dict):
    """Used internally by RRDUpdates"""
    def __init__(self, uuid):
        self.uuid = uuid

# Per Host dictionary (used by RRDUpdates to look up column numbers by variable names)
class HostReport(dict):
    """Used internally by RRDUpdates"""
    def __init__(self, uuid):
        self.uuid = uuid

class RRDUpdates:
    """ Object used to get and parse the output the http://localhost/rrd_udpates?...
    """
    def __init__(self):
        # params are what get passed to the CGI executable in the URL
        self.params = dict()
        self.params['start'] = int(time.time()) - 1000 # For demo purposes!
        self.params['host'] = 'true'   # include data for host (as well as for VMs)
        self.params['cf'] = 'AVERAGE'  # consolidation function, each sample averages 12 from the 5 second RRD
        self.params['interval'] = '60'

    def get_nrows(self):
        return self.rows

    def get_vm_list(self):
        return self.vm_reports.keys()

    def get_vm_param_list(self, uuid):
        report = self.vm_reports[uuid]
        if not report:
            return []
        return report.keys()

    def get_vm_data(self, uuid, param, row):
        report = self.vm_reports[uuid]
        col = report[param]
        return self.__lookup_data(col, row)

    def get_host_uuid(self):
        report = self.host_report
        if not report:
            return None
        return report.uuid

    def get_host_param_list(self):
        report = self.host_report
        if not report:
            return []
        return report.keys()

    def get_host_data(self, param, row):
        report = self.host_report
        col = report[param]
        return self.__lookup_data(col, row)

    def get_row_time(self,row):
        return self.__lookup_timestamp(row)

    # extract float from value (<v>) node by col,row
    def __lookup_data(self, col, row):
        # Note: the <rows> nodes are in reverse chronological order, and comprise
        # a timestamp <t> node, followed by self.columns data <v> nodes
        node = self.data_node.childNodes[self.rows - 1 - row].childNodes[col+1]
        return float(node.firstChild.toxml()) # node.firstChild should have nodeType TEXT_NODE

    # extract int from value (<t>) node by row
    def __lookup_timestamp(self, row):
        # Note: the <rows> nodes are in reverse chronological order, and comprise
        # a timestamp <t> node, followed by self.columns data <v> nodes
        node = self.data_node.childNodes[self.rows - 1 - row].childNodes[0]
        return int(node.firstChild.toxml()) # node.firstChild should have nodeType TEXT_NODE

    def load(self, content):
        xmldoc = minidom.parseString(content)
        self.__parse_xmldoc(xmldoc)
        
    def __parse_xmldoc(self, xmldoc):

        # The 1st node contains meta data (description of the data)
        # The 2nd node contains the data
        self.meta_node = xmldoc.firstChild.childNodes[0]
        self.data_node = xmldoc.firstChild.childNodes[1]

        def lookup_metadata_bytag(name):
            return int (self.meta_node.getElementsByTagName(name)[0].firstChild.toxml())

        # rows = number of samples per variable
        # columns = number of variables
        self.rows = lookup_metadata_bytag('rows')
        self.columns = lookup_metadata_bytag('columns')

        # These indicate the period covered by the data
        self.start_time = lookup_metadata_bytag('start')
        self.step_time  = lookup_metadata_bytag('step')
        self.end_time   = lookup_metadata_bytag('end')

        # the <legend> Node describes the variables
        self.legend = self.meta_node.getElementsByTagName('legend')[0]

        # vm_reports matches uuid to per VM report
        self.vm_reports = {}

        # There is just one host_report and its uuid should not change!
        self.host_report = None

        # Handle each column.  (I.e. each variable)
        for col in range(self.columns):
            self.__handle_col(col)

    def __handle_col(self, col):
        # work out how to interpret col from the legend
        col_meta_data = self.legend.childNodes[col].firstChild.toxml()

        # vm_or_host will be 'vm' or 'host'.  Note that the Control domain counts as a VM!
        (cf, vm_or_host, uuid, param) = col_meta_data.split(':')

        if vm_or_host == 'vm':
            # Create a report for this VM if it doesn't exist
            if not self.vm_reports.has_key(uuid):
                self.vm_reports[uuid] = VMReport(uuid)

            # Update the VMReport with the col data and meta data
            vm_report = self.vm_reports[uuid]
            vm_report[param] = col

        elif vm_or_host == 'host':
            # Create a report for the host if it doesn't exist
            if not self.host_report:
                self.host_report = HostReport(uuid)
            elif self.host_report.uuid != uuid:
                raise PerfMonException, "Host UUID changed: (was %s, is %s)" % (self.host_report.uuid, uuid)

            # Update the HostReport with the col data and meta data
            self.host_report[param] = col

        else:
            raise PerfMonException, "Invalid string in <legend>: %s" % col_meta_data


def get_vm_data(rrd_updates, uuid):
    main = dict()
    main['uuid'] = uuid
    temp = dict()
    main['data'] = temp
    for param in rrd_updates.get_vm_param_list(uuid):
        temp[param] = list()
        #temp[param] = dict()
        if param != "":
            max_time=0
            data=""
            for row in range(rrd_updates.get_nrows()):
                temp1 = dict()
                epoch = rrd_updates.get_row_time(row)
                dv = str(rrd_updates.get_vm_data(uuid,param,row))
                if epoch > max_time:
                    max_time = epoch
                    data = dv
                nt = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(max_time))
                temp1["last_update"] = nt
                temp1["timestamp"] = max_time
                try:
                    if "cpu" in param:
                        temp1["data"] = float(data) * 1000
                    else:
                        temp1["data"] = float(data)
                except Exception:
                    temp1["data"] = 0
                temp[param].append(temp1)
                #temp[param][nt] = data
    return main


# This function receive string arg
# and return list
def converter(arg):
	ret = list()
	obj = RRDUpdates()
	# content maybe with some 'space'
	# so we must do the strip for it
	try:
		obj.load(arg.strip())
	except Exception, e:
		fd = open('py.log', 'w')
		fd.write(arg)
		fd.close()
		print arg.strip()
	try:
		for uuid in obj.get_vm_list():
			ret.append(get_vm_data(obj, uuid))
	except Exception, e:
		print e
		return [[], ""]
	return [ret, json.dumps(ret)]

