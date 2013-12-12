#!--encoding:utf-8--

fields = {
    "rta": u"PING平均返回时间",
    "pl": u"丢包率",
    "load1": u"1分钟内负载",
    "load5": u"5分钟内负载",
    "load15": u"15分钟内负载",
    "users": u"用户",
    "size": u"大小",
    "time": u"时间",
    'vbd_hda_iops_total': u"虚拟磁盘HDA IOPS汇总",
    'vbd_hda_iops_write': u"虚拟磁盘HDA IOPS写",
    'vbd_hdd_read': u"虚拟磁盘HDD读",
    'vbd_hdb_inflight': u"虚拟磁盘HDB I/O队列",
    'vbd_hdd_iops_read': u"虚拟磁盘HDD IOPS写",
    'vbd_hda_inflight': u"虚拟磁盘HDA I/O队列",
    'vbd_hdb_write': u"虚拟磁盘HDB写",
    'vbd_hda_write': u"虚拟磁盘HDA写",
    'vbd_hdb_iops_write': u"虚拟磁盘HDB IOPS写",
    'vbd_hdd_iops_total': u"虚拟磁盘HDD IOPS汇总",
    'vbd_hda_iowait': u"虚拟磁盘HDA I/O等待",
    'vbd_hdd_avgqu_sz': u"虚拟磁盘HDD平均I/O队列长度",
    'memory': u"内存",
    'vbd_hdd_write': u"虚拟磁盘HDD写",
    'vbd_hdd_iops_write': u"虚拟磁盘HDD IOPS写",
    'cpu2': u"CPU2 负载",
    'cpu3': u"CPU3 负载",
    'cpu0': u"CPU0 负载",
    'cpu1': u"CPU1 负载",
    'vif_0_tx': u"第一块虚拟网卡发送",
    'vif_0_rx': u"第一块虚拟网卡接收",
    'vbd_hdb_iowait': u"虚拟磁盘HDB I/O等待",
    'vbd_hdb_avgqu_sz': u"虚拟磁盘HDB平均I/O队列长度",
    'vbd_hda_iops_read': u"虚拟磁盘HDA IOPS读",
    'memory_internal_free': u"内存剩余",
    'vbd_hda_avgqu_sz': u"虚拟磁盘HDA平均I/O队列长度",
    'vbd_hdb_read': u"虚拟磁盘HDB读",
    'vbd_hda_read': u"虚拟磁盘HDA读",
    'vbd_hdb_iops_read': u"虚拟磁盘HDB IOPS读",
    'vbd_hdd_inflight': u"虚拟磁盘HDD I/O队列",
    'vbd_hdb_iops_total': u"虚拟磁盘HDB IOPS汇总",
    'vbd_hdd_iowait': u"虚拟磁盘HDD I/O等待"
}


def convert_field(field):
    new_field = fields.get(field, None)
    if new_field:
        return field + " (%s)" % new_field
    else:
        return field

