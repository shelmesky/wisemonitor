#!--encoding:utf-8--
import xml.dom.minidom


def parse_perfmon_xml(data):
    final_data = []
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
    return final_data


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