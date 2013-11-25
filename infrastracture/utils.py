#! --encoding:utf-8--

import xlwt
import cStringIO
from common.utils import time_stamp_to_string
from logger import logger


def physical_perdata_to_excel(data):
    buf = cStringIO.StringIO()
    book = xlwt.Workbook()
    for filed, value in data.items():
        unit = value['unit']
        sheet = book.add_sheet(filed)
        sheet.write(0, 0, "Time")
        if unit:
            sheet.write(0, 1, "Data (%s)" % unit)
        else:
            sheet.write(0, 1, "Data")
        items = value['data']
        length = len(items)
        for i in range(length):
            js_time_stamp = items[i][0]
            time_stamp = int(js_time_stamp / 1000)
            time_string = time_stamp_to_string(time_stamp)
            
            sheet.write(i+1, 0, time_string)
            sheet.write(i+1, 1, items[i][1])
    
    book.save(buf)
    return buf.getvalue()