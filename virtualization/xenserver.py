# --encoding: utf-8--
from run import global_xenserver_conn
from logger import logger
from pprint import pprint
import XenAPI


def get_xenserver_host_all():
    final_hosts = []
    for ip, session in global_xenserver_conn.items():
        temp = {}
        hosts = session.xenapi.host.get_all()
        temp[ip] = []
        i = 1
        for host in hosts:
            temp_record = {}
            record = session.xenapi.host.get_record(host)
            temp_record['uuid'] = record['uuid']
            temp_record['hostname'] = record['hostname']
            temp_record['address'] = record['address']
            temp_record['cpu_count'] = record['cpu_info']['cpu_count']
            temp_record['cpu_modelname'] = record['cpu_info']['modelname']
            temp_record['version'] = record['software_version']['product_version']
            
            # get all PBDs
            temp_record['PBDs'] = []
            pbds = record['PBDs']
            j = 1
            for pbd in pbds:
                temp_pbd = {}
                pbd_record = session.xenapi.PBD.get_record(pbd)
                sr = pbd_record['SR']
                sr_record = session.xenapi.SR.get_record(sr)
                temp_pbd['pbd_attached'] = pbd_record['currently_attached']
                temp_pbd['pbd_device_config'] = str(pbd_record['device_config'])
                temp_pbd['sr_name'] = sr_record['name_label']
                temp_pbd['sr_size'] = str(int(sr_record['physical_size']) / (1024**3))
                temp_pbd['sr_allocation'] = str(int(sr_record['virtual_allocation']) / (1024**3))
                temp_pbd['sr_utilisation'] = str(int(sr_record['physical_utilisation']) / (1024**3))
                temp_pbd['sr_type'] = sr_record['type']
                temp_pbd['id'] = j
                j += 1
                temp_record['PBDs'].append(temp_pbd)
            
            # get all PIFs
            temp_record['PIFs'] = []
            pifs = record['PIFs']
            k = 1
            for IF in pifs:
                temp_pif = {}
                IF_record = session.xenapi.PIF.get_record(IF)
                temp_pif['ip_config_mode'] = IF_record['ip_configuration_mode']
                temp_pif['is_physical'] = IF_record['physical']
                temp_pif['device'] = IF_record['device']
                temp_pif['is_management'] = IF_record['management']
                temp_pif['IP'] = IF_record['IP']
                temp_pif['netmask'] = IF_record['netmask']
                temp_pif['MAC'] = IF_record['MAC']
                temp_pif['VLAN'] = IF_record['VLAN']
                temp_pif['id'] = k
                k += 1
                temp_record['PIFs'].append(temp_pif)
            
            # get memory parameters in metrics field
            metrics = record['metrics']
            metrics_record = session.xenapi.host_metrics.get_record(metrics)
            temp_record['memory_total'] = int(metrics_record['memory_total']) / (1024**2)
            temp_record['memory_free'] = int(metrics_record['memory_free']) / (1024**2)
            
            temp_record['id'] = i
            i += 1
            
            temp[ip].append(temp_record)
            
        final_hosts.append(temp)
        
    return final_hosts


def get_xenserver_vm_all(host):
    final_vms_record = []
    for ip, session in global_xenserver_conn.items():
        if ip == host:
            vms = session.xenapi.VM.get_all()
            for vm in vms:
                record = session.xenapi.VM.get_record(vm)
                if not record['is_a_template'] and not record['is_control_domain']:
                    temp_record = {}
                    temp_record['uuid'] = record['uuid']
                    temp_record['vcpu_max'] = record['VCPUs_max']
                    temp_record['memory_static_max'] = int(record['memory_static_max']) / (1024**2)
                    temp_record['name_label'] = record['name_label']
                    temp_record['power_state'] = record['power_state']
                    
                    #get network information
                    guest_metrics = record['guest_metrics']
                    guest_metrics_record = session.xenapi.VM_guest_metrics.get_record(guest_metrics)
                    temp_record['networks'] = guest_metrics_record['networks']
                    
                    final_vms_record.append(temp_record)
    
    return final_vms_record
