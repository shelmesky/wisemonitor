SELECT 
nagios_instances.instance_id
,nagios_instances.instance_name
,nagios_servicegroups.servicegroup_id
,nagios_servicegroups.servicegroup_object_id
,obj1.name1 AS servicegroup_name
,nagios_servicegroups.alias AS servicegroup_alias
,nagios_services.service_object_id 
,obj2.name1 AS host_name
,obj2.name2 AS service_description
FROM `nagios_servicegroups` 
INNER JOIN nagios_servicegroup_members ON nagios_servicegroups.servicegroup_id=nagios_servicegroup_members.servicegroup_id 
INNER JOIN nagios_services ON nagios_servicegroup_members.service_object_id=nagios_services.service_object_id
INNER JOIN nagios_objects as obj1 ON nagios_servicegroups.servicegroup_object_id=obj1.object_id
INNER JOIN nagios_objects as obj2 ON nagios_servicegroup_members.service_object_id=obj2.object_id
INNER JOIN nagios_instances ON nagios_servicegroups.instance_id=nagios_instances.instance_id