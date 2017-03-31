# auto_insert_db.py
# Author: wengqiang
# Date Last Modified: 15:13 2017/3/3
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

from flask import Flask
from flask_jsonrpc import JSONRPC
from datetime import datetime
import time
import MySQLdb

DATABASE_HOST = "127.0.0.1"
DATABASE_DB = "lottery_test"
DATABASE_USER = "wens07"
DATABASE_PASSWD = "6556163"
DATABASE_PORT = 3306


def connect_db():
    """
    connect to the target db
    :return:
    """

    try:
        conn = MySQLdb.connect(host=DATABASE_HOST, port=DATABASE_PORT,
                               user=DATABASE_USER, passwd=DATABASE_PASSWD,
                               db=DATABASE_DB)

    except MySQLdb.Error as err:
        print("mysql error: {}".format(err))
        return None

    return conn


def insert_data():
    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()
    game_issue = 0

    while True:
        game_issue = game_issue + 1
        create_time = datetime.now()
        game_state = 0
        command = "insert into tbl_game_info (game_issue, game_state, create_time) values ('{}', '{}', '{}')".format(
            game_issue, game_state, create_time)

        db_cusor.execute(command)
        db_conn.commit()

        time.sleep(26)

        create_time = datetime.now()
        game_state = 1
        command = "update tbl_game_info set game_state={} where game_issue={}".format(
            game_state, game_issue)

        db_cusor.execute(command)
        db_conn.commit()

        time.sleep(24)

        create_time = datetime.now()
        game_state = 3
        command = "update tbl_game_info set game_state={} where game_issue={}".format(
            game_state, game_issue)

        db_cusor.execute(command)
        db_conn.commit()



if __name__ == '__main__':
    insert_data()