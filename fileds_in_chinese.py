#!--encoding:utf-8--

fields = {
    "rta": "PING平均返回时间",
    "pl": "丢包率",
    "load1": "1分钟内负载",
    "load5": "5分钟内负载",
    "load15": "15分钟内负载",
    "users": "用户",
    "size": "大小",
    "time": "时间",
    'vbd_hda_iops_total': "虚拟磁盘HDA IOPS汇总",
    'vbd_hda_iops_write': "虚拟磁盘HDA IOPS写",
    'vbd_hdd_read': "虚拟磁盘HDD读",
    'vbd_hdb_inflight': "虚拟磁盘HDB I/O队列",
    'vbd_hdd_iops_read': "虚拟磁盘HDD IOPS写",
    'vbd_hda_inflight': "虚拟磁盘HDA I/O队列",
    'vbd_hdb_write': "虚拟磁盘HDB写",
    'vbd_hda_write': "虚拟磁盘HDA写",
    'vbd_hdb_iops_write': "虚拟磁盘HDB IOPS写",
    'vbd_hdd_iops_total': "虚拟磁盘HDD IOPS汇总",
    'vbd_hda_iowait': "虚拟磁盘HDA I/O等待",
    'vbd_hdd_avgqu_sz': "虚拟磁盘HDD平均I/O队列长度",
    'memory': "内存",
    'vbd_hdd_write': "虚拟磁盘HDD写",
    'vbd_hdd_iops_write': "虚拟磁盘HDD IOPS写",
    'cpu2': "CPU2 负载",
    'cpu3': "CPU3 负载",
    'cpu0': "CPU0 负载",
    'cpu1': "CPU1 负载",
    'vif_0_tx': "第一块虚拟网卡发送",
    'vif_0_rx': "第一块虚拟网卡接收",
    'vbd_hdb_iowait': "虚拟磁盘HDB I/O等待",
    'vbd_hdb_avgqu_sz': "虚拟磁盘HDB平均I/O队列长度",
    'vbd_hda_iops_read': "虚拟磁盘HDA IOPS读",
    'memory_internal_free': "内存剩余",
    'vbd_hda_avgqu_sz': "虚拟磁盘HDA平均I/O队列长度",
    'vbd_hdb_read': "虚拟磁盘HDB读",
    'vbd_hda_read': "虚拟磁盘HDA读",
    'vbd_hdb_iops_read': "虚拟磁盘HDB IOPS读",
    'vbd_hdd_inflight': "虚拟磁盘HDD I/O队列",
    'vbd_hdb_iops_total': "虚拟磁盘HDB IOPS汇总",
    'vbd_hdd_iowait': "虚拟磁盘HDD I/O等待"
}


def convert_unit(unit):
    new_field = fields.get(unit, None)
    if new_filed:
        return unit + " (%s)" % new_field
    else:
        return unit

