#!--encoding:utf-8--

import os
import fcntl
from tornado import ioloop


def make_pipe():
    """
    创建两个匿名管道
    设置为非阻塞，使用tornado的ioloop监测其读写事件
    用户发送从nagios/xenserver接收到的报警到主线程
    """
    nagios_read_fd, nagios_write_fd = os.pipe()
    
    flags = fcntl.fcntl(nagios_read_fd, fcntl.F_GETFL)
    fcntl.fcntl(nagios_read_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    flags = fcntl.fcntl(nagios_write_fd, fcntl.F_GETFL)
    fcntl.fcntl(nagios_write_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    xen_read_fd, xen_write_fd = os.pipe()
    
    flags = fcntl.fcntl(xen_read_fd, fcntl.F_GETFL)
    fcntl.fcntl(xen_read_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    flags = fcntl.fcntl(xen_write_fd, fcntl.F_GETFL)
    fcntl.fcntl(xen_write_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    return nagios_read_fd, nagios_write_fd, xen_read_fd, xen_write_fd


if __name__ == '__main__':
    # make simple test
    def nagios_read_handler(fd, events):
        print os.read(fd, 1024)
    
    nagios_read, nagios_write, xen_read, xen_write = make_pipe()
        
    ioloop = ioloop.IOLoop().instance()
    ioloop.add_handler(nagios_read, nagios_read_handler, ioloop.READ)
    ioloop.add_handler(xen_read, nagios_read_handler, ioloop.READ)
    os.write(nagios_write, "hello nagios\n")
    os.write(xen_write, "hello xenserver\n")
    ioloop.start()
    