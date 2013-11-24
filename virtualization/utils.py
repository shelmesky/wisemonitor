#!--encoding:utf-8--
import xml.dom.minidom


xml_config_str = "<config>%s</config>"
xml_config_empty = "<config></config>"

xml_str = """<variable>
<name value="%s"/>
<alarm_trigger_level value="%s"/>
<alarm_trigger_period value="%s"/>
<alarm_auto_inhibit_period value="%s"/>
</variable>"""


def generate_perfmon_xml(data):
    global_period = data.get("global_period", None)
    if not global_period and global_period != 0:
        return False
    
    global_period = data.get("global_period", None)
    
    cpu_name = "cpu_usage"
    cpu_level = data.get("cpu_level", None)
    cpu_period = data.get("cpu_period", None)
    
    network_name = "network_usage"
    network_level = data.get("network_level", None)
    network_period = data.get("network_period", None)
    
    disk_name = "disk_usage"
    disk_level = data.get("disk_level", None)
    disk_period = data.get("disk_period", None)
    
    xml_content = ""
    
    if cpu_level and cpu_period:
        cpu_xml_str = xml_str % (
            cpu_name, cpu_level, cpu_period, global_period
        )
        xml_content += cpu_xml_str
    
    if network_level and network_period:
        network_xml_str = xml_str % (
            network_name, network_level, network_period, global_period
        )
        xml_content += network_xml_str

    if disk_level and disk_period:
        disk_xml_str = xml_str % (
            disk_name, disk_level, disk_period, global_period
        )
        xml_content += disk_xml_str
    
    return xml_config_str % xml_content


def parse_perfmon_xml(data):
    final_data = []
    
    if not data or data == xml_config_empty:
        usage_name = ["cpu_usage", "network_usage", "disk_usage"]
        for name_value in usage_name:
            temp = {}
            temp['name'] = name_value
            temp['alarm_trigger_level'] = 0
            temp['alarm_trigger_period'] = 0
            temp['alarm_auto_inhibit_period'] = 0
            final_data.append(temp)
        
        return final_data, True
    
    doc = xml.dom.minidom.parseString(data)
    for node in doc.getElementsByTagName("variable"):
        temp = {}
        
        name_node = node.getElementsByTagName("name")
        name_value = name_node[0].getAttribute("value")
        
        level_node = node.getElementsByTagName("alarm_trigger_level")
        level_value = level_node[0].getAttribute("value")
        
        period_node = node.getElementsByTagName("alarm_trigger_period")
        period_value = period_node[0].getAttribute("value")
        
        inhibit_period_node = node.getElementsByTagName("alarm_auto_inhibit_period")
        inhibit_period_value = inhibit_period_node[0].getAttribute("value")
        
        temp['name'] = name_value
        temp['alarm_trigger_level'] = level_value
        temp['alarm_trigger_period'] = period_value
        temp['alarm_auto_inhibit_period'] = inhibit_period_value
        final_data.append(temp)
    return final_data, False


if __name__ == '__main__':
    xml_str = """<config>
                    <variable>
                        <name value="cpu_usage" />
                        <alarm_trigger_level value="0.5" />
                        <alarm_trigger_period value="60" />
                        <alarm_auto_inhibit_period value="3600" />
                    </variable>
                    <variable>
                        <name value="network_usage" />
                        <alarm_trigger_level value="102400" />
                        <alarm_trigger_period value="60" />
                        <alarm_auto_inhibit_period value="3600" />
                    </variable>
                    <variable>
                        <name value="disk_usage" />
                        <alarm_trigger_level value="1024000" />
                        <alarm_trigger_period value="60" />
                        <alarm_auto_inhibit_period value="3600" />
                    </variable>
                </config>"""
    
    print parse_perfmon_xml(xml_str)