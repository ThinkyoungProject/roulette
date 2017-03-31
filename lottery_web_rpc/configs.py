# db_config.py
# Author: wengqiang
# Date Last Modified: 10:06 2017/2/22
#
# Changelog:
#  
#     
#
# Usage:
#    
#     

#!/usr/bin/env python
# coding=utf-8


class DevelopmentConfig:
    """
    :return:
    """
    DEBUG = True

    DATABASE_HOST = "127.0.0.1"
    DATABASE_DB = "lottery_web_rpc"
    DATABASE_USER = "wens07"
    DATABASE_PASSWD = "6556163"
    DATABASE_PORT = 3306
    DATABASE_CHARSET = 'utf8'

class AliyunConfig:
    """
    :return
    """
    DEBUG = True

    DATABASE_HOST = "127.0.0.1"
    DATABASE_DB = "lottery_web_rpc"
    DATABASE_USER = "root"
    DATABASE_PASSWD = "70baf88c78293c487443c647b800566b"
    DATABASE_PORT = 3306
    DATABASE_CHARSET = 'utf8'

class AwsConfig:
    """
    :return
    """

    DEBUG = True
    DATABASE_HOST = "52.80.29.33"
    DATABASE_DB = "lottery_web_rpc"
    DATABASE_USER = "chain_monitor"
    DATABASE_PASSWD = "time.9818"
    DATABASE_PORT = 3306
    DATABASE_CHARSET = 'utf8'
