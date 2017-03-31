#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'

import logging

# RPC configure
RPC_SERVER_IP = "127.0.0.1"
RPC_SERVER_PORT = 62131
RPC_USER = "a"
RPC_PASS = "b"
RPC_COROUTINE_MAX = 50

# DB configure
DB_IP = "115.28.142.164"
DB_PORT = 3306
DB_NAME = "lottery_web_rpc"
DB_USER = "root"
DB_PASS = "70baf88c78293c487443c647b800566b"
DB_POOL_SIZE = 10
CONNECT_TIMEOUT = 50

# SYNC configure
SYNC_BLOCK_PER_ROUND = 1000

# LOG configure
LOG_LEVEL = logging.DEBUG
LOG_FILENAME = "data_collector.log"


