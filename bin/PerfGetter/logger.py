import os
import sys
import logging
import logging.config
from logging import handlers
import settings

DEBUG = True

SYSLOG_HANDLER_HOST = 'localhost'

LOG_PATH = settings.LOG_PATH

MAIL_HANDLER_HOST = 'smtp.qq.com'
MAIL_HANDLER_FROMADDR = 'user@qq.com'
MAIL_HANDLER_TOADDRS = ['user1@qq.com','user2@gmail.com']
MAIL_HANDLER_SUBJECT = 'Logging from python app'
MAIL_HANDLER_CREDENTIALS = ('user@qq.com','password')

TCPSOCKET_HANDLER_HOST = 'localhost'
TCPSOCKET_HANDLER_PORT = 9022

UDPSOCKET_HANDLER_HOST = 'localhost'
UDPSOCKET_HANDLER_PORT = 9021

NTEVENT_HANDLER_APPNAME = 'Python Application'
NTEVENT_HANDLER_LOGTYPE = 'Application'

HTTP_HANDLER_HOST = 'localhost:8000'
HTTP_HANDLER_URL = '/logging'
HTTP_HANDLER_METHOD = 'GET'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
       'detail': {
            'format': '%(name)s %(levelname)s %(asctime)s %(module)s %(process)d %(thread)d [%(pathname)s:%(lineno)d] %(message)s'
        },
        'verbose': {
            'format': '%(name)s %(levelname)s %(asctime)s [%(pathname)s:%(lineno)d] %(message)s'
        },
        'simple': {
            'format': '%(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
       'console':{
            'level':'NOTSET',
            'class':'logging.StreamHandler',
            'stream':sys.stderr,
            'formatter': 'verbose' #'simple'
        },
        'file':{
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.getcwd(), LOG_PATH),
            'formatter': 'verbose',
            'maxBytes': 1024*1024*20,  # 20MB
            'backupCount': 5,
        },
        'syslog.remote':{
            'level':'DEBUG',
            'class':'logging.handlers.SysLogHandler',
            'address':(SYSLOG_HANDLER_HOST,handlers.SYSLOG_UDP_PORT), # log to syslog or rsyslog server
            'formatter': 'verbose',
        },
        'mail.handler':{
            'level':'DEBUG',
            'class':'logging.handlers.SMTPHandler', # log to mailbox
            'mailhost':MAIL_HANDLER_HOST,
            'fromaddr':MAIL_HANDLER_FROMADDR,
            'toaddrs':MAIL_HANDLER_TOADDRS,
            'subject':MAIL_HANDLER_SUBJECT,
            'credentials':MAIL_HANDLER_CREDENTIALS,
            'formatter': 'detail',
        },
        'socket.tcp.handler':{
            'level':'DEBUG',
            'class':'logging.handlers.SocketHandler', # log to tcp socket
            'host':TCPSOCKET_HANDLER_HOST,
            'port':TCPSOCKET_HANDLER_PORT,
            'formatter': 'verbose',
        },
        'socket.udp.handler':{
            'level':'DEBUG',
            'class':'logging.handlers.DatagramHandler', # log to udp socket
            'host':UDPSOCKET_HANDLER_HOST,
            'port':UDPSOCKET_HANDLER_PORT,
            'formatter': 'verbose',
        },
        'http.handler':{
            'level':'DEBUG',
            'class':'logging.handlers.HTTPHandler', # log to http server
            'host':HTTP_HANDLER_HOST,
            'url':HTTP_HANDLER_URL,
            'method':HTTP_HANDLER_METHOD,
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'CommonLogger': {
            'handlers': ['console', 'file'] if DEBUG else ['file'],
            'level': 'DEBUG' if DEBUG else 'DEBUG', #'INFO'
            'propagate': False,
            # very important in multithread environment, means disable propagation from current logger to the *root* logger.
        },
    }
}

syslog_local = {
            'level':'DEBUG',
            'class':'logging.handlers.SysLogHandler',
            'address':'/dev/log', # log to local syslog file
            'formatter': 'verbose',
        }

ntevent_handler = {
            'level':'DEBUG',
            'class':'logging.handlers.NTEventLogHandler', # log to windows event log
            'appname':NTEVENT_HANDLER_APPNAME,
            'logtype':NTEVENT_HANDLER_LOGTYPE,
            'formatter': 'verbose',
        }

common_logger = {
            'handlers': ['console', 'file'] if DEBUG else ['file'],
            'level': 'DEBUG' if DEBUG else 'DEBUG', #'INFO'
            'propagate': False,
            # very important in multithread environment, means disable propagation from current logger to the *root* logger.
        }


if sys.platform == 'linux2':
    LOGGING['handlers']['syslog.local'] = syslog_local
if sys.platform == 'win32':
    LOGGING['handlers']['ntevent.handler'] = ntevent_handler

def getlogger(logger_name=None):
    if isinstance(logger_name,str) or isinstance(logger_name,unicode):
        LOGGING['loggers'][logger_name] = common_logger
        logging.config.dictConfig(LOGGING)
        logger = logging.getLogger(logger_name)
    else:
        logging.config.dictConfig(LOGGING)
        logger = logging.getLogger("CommonLogger")
        
    return logger

logger = getlogger(settings.LOG_INSTANCE)
