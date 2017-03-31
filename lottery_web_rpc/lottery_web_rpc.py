# lottery_web_rpc.py
# Author: wengqiang
# Date Last Modified: 13:50 2017/2/22
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

from flask import Flask, session, Response, request
from flask_jsonrpc import JSONRPC
from datetime import datetime, date, time
# from flask_session import Session
from logging.handlers import RotatingFileHandler
from  uuid import uuid4
import MySQLdb
import psutil

import time
import re


app = Flask(__name__)
# app.config.from_object('configs.AwsConfig')
app.config.from_object('configs.DevelopmentConfig')
# app.config.from_object('configs.AliyunConfig')
#print(app.config.get('DATABASE_HOST'))


#jsonrpc for web_front
jsonrpc = JSONRPC(app=app, service_url="/api", enable_web_browsable_api=True)
handler = RotatingFileHandler('lottery_web_rpc.log', maxBytes=10000, backupCount=1)


def generate_sid():
    return str(uuid4())

def connect_db():
    """
    connect to the target db
    :return:
    """

    try:
        conn = MySQLdb.connect(host=app.config['DATABASE_HOST'], port=app.config['DATABASE_PORT'],
                               user=app.config['DATABASE_USER'], passwd=app.config['DATABASE_PASSWD'],
                               db=app.config['DATABASE_DB'], charset=app.config['DATABASE_CHARSET'] )

    except MySQLdb.Error as err:
        print("mysql error: {}".format(err))
        return None

    return conn

def user_name_check(p_usr_name):
    """
    检查用户名是否合法

    :param p_usr_name:
    :return:
    legal:    True
    illegal:  False
    """

    match_result = re.fullmatch(r'^[a-zA-Z][a-zA-Z0-9_]{3,19}', p_usr_name)

    if None == match_result:
        return False

    return True

def user_phone_check(p_usr_phone):
    """
    检查手机号是否合法

    :param p_usr_phone:
    :return:
    legal:    True
    illegal:  False
    """

    match_result = re.fullmatch(r'^[1-9][0-9]{10}', p_usr_phone)

    if None == match_result:
        return  False

    return  True

def user_passwd_check(p_usr_passwd):
    """
    检查用户密码是否合法

    :param p_usr_passwd:
    :return:

    legal:    True
    illegal:  False
    """

    match_result = re.fullmatch(r'[0-9]{6}', p_usr_passwd)

    if None == match_result:
        return  False

    return True

def robot_whether_running(p_robot_thread_name):
    """
    检查后端机器人是否正常工作

    :return:
    false：mean robot stop
    true:  mean robot is running
    """
    for proc in psutil.process_iter():
        if proc.name() == p_robot_thread_name:
            print(proc.name())
            return  True
    return False


@jsonrpc.method(name="info")
def info():
    return {"info": "this is the rpc web-end for lottery smart contract demo."}

@jsonrpc.method(name="test_session")
def test_session(p_usr_sid=""):
    return session["phone"]

@jsonrpc.method(name="user_register")
def user_register(p_usr_name, p_usr_phone, p_usr_passwd):
    """
    将注册用户数据插入到数据库中
    :param p_usr_name:
    :param p_usr_phone:
    :param p_usr_passwd:
    :return:
    success: {'success': 1}
    fail:    {'error': "error related info"}
    """

    if user_name_check(p_usr_name) == False:
        return {'error': "用户名非法!", 'rule': "以大小写字母开头，长度为4~20, 后面可以是_, 大小写字母 或者 0~9字符"}

    if user_phone_check(p_usr_phone) == False:
        return {'error': "用户手机号非法!", 'rule': "11位数字, 不能以0开头"}

    if user_passwd_check(p_usr_passwd) == False:
        return {'error': "用户密码非法!", 'rule': "6位数字"}

    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "不能连接到数据库!"}

    db_cusor = db_conn.cursor()

    try:
        # check user phone and user name
        command = "select user_phone from tbl_user"
        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "数据库错误: {}".format(err)}

    for i in range(affected_rows):
        user_phone = db_cusor.fetchone()
        if p_usr_phone == user_phone[0]:
            return {'error': "用户手机号重复!", 'rule': "11位数字, 不能以0开头"}

    try:
        command = "select user_name from tbl_user"
        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "数据库错误: {}".format(err)}

    for i in range(affected_rows):
        user_name = db_cusor.fetchone()
        if p_usr_name == user_name[0]:
            return {'error': "用户名重复!", 'rule': "以大小写字母开头，长度为4~20, 后面可以是_, 大小写字母 或者 0~9字符"}


    db_user_create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        command = "insert into tbl_user (user_phone, user_password, user_name, create_time) values ('{}', '{}', '{}', '{}')".format(
                p_usr_phone, p_usr_passwd, p_usr_name, db_user_create_time)

        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "数据库错误: {}".format(err)}

    # if 0 == affected_rows:
    #     return {'error': "error happens when insert into db!"}

    db_conn.commit()
    db_conn.close()

    return {'success': 1}


@jsonrpc.method(name="user_login")
def user_login(p_usr, p_usr_passwd):
    """
     验证用户是否可以登录

    :param p_usr:
    :param p_usr_passwd:
    :return:
    success: {'success': 1}
    fail:    {'error': "error related info"}
    """
    # if p_usr_phone != "" and user_phone_check(p_usr_phone) == False:
    #     return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}
    #
    # if p_usr_name != "" and user_name_check(p_usr_name) == False:
    #     return {'error': "user name is illegal!", 'rule': "start with lowercase/upcase character, length of 4~20, should be _, lowercase/uppercase character or number of 0~9"}
    #
    # if user_passwd_check(p_usr_passwd) == False:
    #     return {'error': "user password is illegal", 'rule': "should be length of 6"}

    # print(app.permanent_session_lifetime)
    if type(p_usr) != str:
        return {'error': "登录名需要是string类型!"}
    p_usr_phone = ""
    p_usr_name = ""
    result_sid = generate_sid()

    if user_phone_check(p_usr):
        p_usr_phone = p_usr
    elif user_name_check(p_usr):
        p_usr_name = p_usr
    else:
        return {'error': "用户手机号或用户名非法", 'user_phone_rule': "11位数字，不能以0开头", \
                'user_name_rule': "以大小写字符开头，长度为4~20, 后面可以是_, 大小写字母 或者 0~9字符"}


    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "不能连接到数据库！"}

    db_cusor = db_conn.cursor()

    if p_usr_phone != "":
        command = "select user_password from tbl_user where user_phone = '{}'".format(p_usr_phone)
    elif p_usr_name != "":
        command = "select user_password from tbl_user where binary user_name = '{}'".format(p_usr_name)
    else:
        return {'error': "登录需要输入用户手机号或者用户名"}

    try:
        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "数据库错误: {}".format(err)}


    # no this user
    if 0 == affected_rows:
        return {'error': "用户不存在!"}
    else:
        db_user_passwd = db_cusor.fetchone()
        passwd = db_user_passwd[0]
        if passwd != p_usr_passwd:
            return {'error': "用户密码不正确!", 'rule': "长度为6，可以是0~9的数字"}

        # print(session.sid)
        # user_sid = lottery_session.generate_sid()

        if p_usr_phone != "":
            session["phone"] = p_usr_phone
        else:
            try:
                command = "select user_phone from tbl_user where binary user_name = '{}'".format(p_usr_name)
                affected_rows = db_cusor.execute(command)
            except MySQLdb.Error as err:
                return {'error': "数据库错误: {}".format(err)}

            db_usr_phone = db_cusor.fetchone()
            session["phone"] = db_usr_phone[0]


        # print(session.sid)
        # print(app.session_cookie_name)

        app.session_cookie_name = "login_session"
        respose = Response()
        respose.headers["session_sid"] = result_sid
        respose.set_cookie(app.session_cookie_name)
        db_conn.close()
        return {'success': 1, 'session_id': result_sid}
        # return respose




@jsonrpc.method(name="get_server_state")
def get_server_state(p_game_issue=""):
    """
    获取服务器状态

    :param p_game_issue:
    :return:
    success: {'success': 1, , 'game_issue': game_issue, 'game_state': game_state, 'continue-time': continue_time}
    fail:    {'error': "error related info
    """
    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()


    if "" == p_game_issue:
        try:
            command = "select game_issue, game_state, create_time from tbl_game_info where game_issue=(select max(game_issue) from tbl_game_info)"
            affected_rows = db_cusor.execute(command)
        except MySQLdb.Error as err:
            return {'error': "mysql error: {}".format(err)}


    else:
        if type(p_game_issue) != int:
            return {'error': "game issue should be a number!"}

        try:
            command = "select game_issue, game_state, create_time from tbl_game_info where game_issue={}".format(p_game_issue)
            affected_rows = db_cusor.execute(command)
        except MySQLdb.Error as err:
            return {'error': "mysql error: {}".format(err)}


    if 0 == affected_rows:
        return {'error': "no game has been started!"}

    db_server_state = db_cusor.fetchone()

    game_issue = db_server_state[0]
    game_state = db_server_state[1]
    create_time = db_server_state[2]

    server_time = datetime.now()
    time_interval = (server_time - create_time).total_seconds()

    app.logger.info("game_issue: %s, game_state: %s, create_time: %s", game_issue, game_state, create_time)
    app.logger.info("server_time: %s, time_interval: %s",server_time, time_interval)
    # print(time_interval)
    # print(game_issue, game_state, create_time)
    # print(server_time)
    # print((server_time - create_time).total_seconds())
    # time of starting bet
    if 0 == game_state:
        result = 30 - time_interval
        app.logger.info("result: %s\n", result)
        if round(result) < 2:
            result = 2

    elif 1 == game_state:
        result = 20 - (time_interval - 30)
        app.logger.info("result: %s\n", result)
        if round(result) < 2:
            result = 2
    elif 2 == game_state:
        result = 10 - (time_interval - 50)
        app.logger.info("result: %s\n", result)
        if round(result) < 2:
            result = 2

    else:
        result = 0
        # try:
        #     command = "delete from tbl_rolling_message"
        #     affected_rows = db_cusor.execute(command)
        # except MySQLdb.Error as err:
        #     return {'error': "mysql error: {}".format(err)}

        app.logger.info("result: %s\n", result)

    db_conn.close()
    result = round(result)
    return {'success': 1, 'game_issue': game_issue, 'game_state': game_state, 'continue_time': result}




@jsonrpc.method(name="get_user_balance")
def get_user_balance(p_usr_sid=""):
    """
    获取用户余额
    :param p_usr_sid:

    :return:
    success: {'success': 1, 'user_balance': balance}
    fail:    {'error': "error related info"}
    """
    # if user_phone_check(p_usr_phone) == False:
    #     return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}

    if type(p_usr_sid) != str:
        return {'error': "usr sid should be a string!"}

    p_usr_phone = session.get("phone")
    if p_usr_phone == None:
        return {'error': "invalid usr sid"}


    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:
        command = "select user_balance from tbl_user where user_phone='{}'".format(p_usr_phone)
        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}

    if 0 == affected_rows:
        return {'error': "no this user!"}

    db_user_balance = db_cusor.fetchone()
    user_balance = db_user_balance[0]

    db_conn.close()
    return {'success': 1, "user_balance": user_balance}

@jsonrpc.method(name="clear_user_bet_info")
def clear_user_bet_info(p_usr_sid=""):
    """
    清除用户本轮的投注信息

    :param p_usr_sid:
    :return:
    """
    # if user_phone_check(p_usr_phone) == False:
    #     return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}

    if type(p_usr_sid) != str:
        return {'error': "usr sid should be  a string!"}

    p_usr_phone = session.get("phone")
    if p_usr_phone == None:
        return {'error': "invalid usr sid"}

    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:
        # first, get game issue
        command = "select max(game_issue) from tbl_game_info"
        affected_rows = db_cusor.execute(command)
        if 0 == affected_rows:
            return {'error': "no such data!"}
        db_game_issue = db_cusor.fetchone()
        game_issue = db_game_issue[0]

        command = "select game_state from tbl_game_info where game_issue={}".format(game_issue)
        affected_rows = db_cusor.execute(command)
        game_state = db_cusor.fetchone()
        # print(type(game_state), game_state)
        if 0 != game_state[0]:
            return {'error': "cannot revert bet at current time!"}

        command = "select game_pot from tbl_game_info where game_issue=(select max(game_issue) from tbl_game_info)"
        affected_rows = db_cusor.execute(command)
        db_game_pot = db_cusor.fetchone()
        game_pot = db_game_pot[0]

        command = "select lottery_amount from tbl_lottery where user_phone='{}' and game_issue={}".format(p_usr_phone, game_issue)
        affected_rows = db_cusor.execute(command)
        for i in range(affected_rows):
            db_amount = db_cusor.fetchone()
            game_pot = game_pot - int(db_amount[0])

        command = "update tbl_game_info set game_pot = {} where game_issue={}".format(game_pot, game_issue)
        affected_rows = db_cusor.execute(command)
        db_conn.commit()

        command = "delete from tbl_lottery where user_phone='{}' and game_issue={}".format(p_usr_phone, game_issue)
        affected_rows = db_cusor.execute(command)
        command = "delete from tbl_message where game_issue={}".format(game_issue)
        affected_rows = db_cusor.execute(command)

        # command = "select user_name from tbl_user where user_phone='{}'".format(p_usr_phone)
        # affected_rows = db_cusor.execute(command)
        # db_user_name = db_cusor.fetchone()
        # user_name = db_user_name[0]
        command = "delete from tbl_rolling_message where user_phone='{}'".format(p_usr_phone)
        affected_rows = db_cusor.execute(command)

    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}


    db_conn.commit()
    db_conn.close()

    return {'success': 1}

@jsonrpc.method(name="set_user_bet_info")
def set_user_bet_info(p_game_issue, p_usr_bet_info_list, p_usr_sid=""):
    """
    向数据库设置用户的投注信息

    :param p_usr_sid:
    :param p_game_issue:
    :param p_usr_bet_area_list:
    :param p_usr_bet_amount_list:
    :return:
    success: {'success': 1}
    fail:    {'error': "error related info"}
    """
    # if user_phone_check(p_usr_phone) == False:
    #     return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}
    if type(p_usr_sid) != str:
        return {'error': "usr sid should be  a string!"}

    p_usr_phone = session.get("phone")
    if p_usr_phone == None:
        return {'error': "invalid usr sid"}

    if type(p_game_issue) != int:
        return {'error': "game issue should be a number!"}
    if type(p_usr_bet_info_list) != str:
        return {'error': "bet info list should be a string!"}

    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:
        command = "select game_state from tbl_game_info where game_issue={}".format(p_game_issue)
        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}

    if 0 == affected_rows:
        return {'error': "no such game issue!"}

    game_state = db_cusor.fetchone()
    # print(type(game_state), game_state)
    if 0 != game_state[0]:
        return {'error': "cannot bet at current time!"}

    # # insert rolling message
    # command = "select message_id, message_value from tbl_message where game_issue=(select max(game_issue) from tbl_message  where message_type=2)  and message_type=2"
    # affected_rows = db_cusor.execute(command)
    # for i in range(affected_rows):
    #     each_row = db_cusor.fetchone()
    #     command = "insert into tbl_rolling_message (message_value) value ('{}')".format(each_row[1])
    #     affected_rows = db_cusor.execute(command)
    #     db_conn.commit()


    user_bet_info = list(p_usr_bet_info_list.split(','))
    # print(user_bet_info)

    for i in range(0, len(user_bet_info), 2):
        # print(i)
        db_user_create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        try:
            command = "insert into tbl_lottery (user_phone, game_issue, lottery_number, lottery_amount, create_time) \
                          values('{}', {}, {}, {}, '{}')".format(p_usr_phone, p_game_issue, user_bet_info[i], user_bet_info[i + 1], db_user_create_time)
            affected_rows = db_cusor.execute(command)
            db_conn.commit()

            command = "select game_pot from tbl_game_info where game_issue=(select max(game_issue) from tbl_game_info)"
            affected_rows = db_cusor.execute(command)
            db_game_pot = db_cusor.fetchone()
            game_pot = db_game_pot[0]
            game_pot = game_pot + int(user_bet_info[i + 1])
            command = "update tbl_game_info set game_pot = {} where game_issue={}".format(game_pot, p_game_issue)
            affected_rows = db_cusor.execute(command)
            db_conn.commit()


            command = "select user_name from tbl_user where user_phone='{}'".format(p_usr_phone)
            affected_rows = db_cusor.execute(command)
            db_user_name = db_cusor.fetchone()
            user_name = db_user_name[0]

            lottery_area = ["", "恭喜", "发财", "福星", "高照", "万事", "如意"]
            bet_area = lottery_area[int(user_bet_info[i])]
            message = ("{}在{}区域押注{}元宝".format(user_name, bet_area, str.strip(user_bet_info[i + 1])))

            command = "insert into tbl_message (message_value, game_issue) value ('{}', {})".format(message, p_game_issue)
            affected_rows = db_cusor.execute(command)
            db_conn.commit()

            command = "insert into tbl_rolling_message (message_value, user_phone) value ('{}', '{}')".format(message, p_usr_phone)
            affected_rows = db_cusor.execute(command)
            db_conn.commit()

        except MySQLdb.Error as err:
            return {'error': "mysql error: {}".format(err)}


    db_conn.close()
    return {'success': 1}


@jsonrpc.method(name="get_lottery_pond_amount")
def get_lottery_pond_amount():
    """
    获取奖池的总金额


    :return:
    success: {'success': 1, 'lottery_pond': amount}
    fail:    {'error': "error related info"}
    """
    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:
        command = "select game_pot from tbl_game_info where game_issue=(select max(game_issue) from tbl_game_info)"
        affected_rows = db_cusor.execute(command)
    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}

    if 0 == affected_rows:
        return {'error': "no such data!"}


    db_game_pond = db_cusor.fetchone()
    db_conn.close()

    return {'success': 1, "lottery_pond": db_game_pond}




@jsonrpc.method(name="get_rolling_windows_info")
def get_rolling_windows_info(p_message_id=0, p_message_num=10):
    """
    获取滚动窗口所需的信息

    :param: p_message_num
    :return:
    success: {'success': 1, 'data': 所需滚动信息}
    fail:    {'error': "error related info"}
    """
    if type(p_message_id) != int:
        return {'error': "message id should be a number!"}
    if type(p_message_num) != int:
        return {'error': "message num should be a number!"}

    if p_message_id == 0:
        p_message_id = 1

    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:

        command = "select max(message_id) from tbl_rolling_message"
        affected_rows = db_cusor.execute(command)
        db_message_id = db_cusor.fetchone()
        global_max_message_id = db_message_id[0]

        command = "select message_id, message_value from tbl_rolling_message where message_id>={} limit {}".format(p_message_id, p_message_num)
        affected_rows = db_cusor.execute(command)

        if 0 == affected_rows:
            return {'error': "no such data!"}

        db_data = []
        db_message_id = p_message_id
        for i in range(affected_rows):
            each_row = db_cusor.fetchone()
            db_message_id = each_row[0]
            db_data.append(each_row[1])

        if db_message_id == global_max_message_id:
            command = "select min(message_id) from tbl_rolling_message where game_issue=(select max(game_issue) from tbl_rolling_message)"
            affected_rows = db_cusor.execute(command)
            db_message_id = db_cusor.fetchone()
            global_min_message_id = db_message_id[0]
            db_message_id = global_min_message_id - 1

    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}

    db_conn.commit()
    db_conn.close()

    return {'success': 1, 'message_id':db_message_id + 1, 'data':db_data}



@jsonrpc.method(name="get_lottery_opening_result")
def get_lottery_opening_result(p_usr_sid=""):
    """
    获取博彩合约上次的开奖结果

    :param p_usr_sid:
    :return:
    """
    # if user_phone_check(p_usr_phone) == False:
    #     return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}
    if type(p_usr_sid) != str:
        return {'error': "usr sid should be  a string!"}
    p_usr_phone = session.get("phone")
    if p_usr_phone == None:
        return {'error': "invalid usr sid"}


    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:

        # first, get the last game issue
        command = "select max(game_issue) from tbl_game_info"
        affected_rows = db_cusor.execute(command)
        if 0 == affected_rows:
            return {'error': "no such data!"}
        db_game_issue = db_cusor.fetchone()
        game_issue = db_game_issue[0] - 1

        command = "select game_result from tbl_game_info where game_issue= {}".format(game_issue)
        affected_rows = db_cusor.execute(command)
        if 0 == affected_rows:
            return {'error': "no such data!"}
        db_game_result = db_cusor.fetchone()
        game_result = db_game_result[0]

        command = "select sum(lottery_bonus) from tbl_lottery where game_issue={} and lottery_number={} and user_phone='{}'".format(game_issue, game_result, p_usr_phone)
        affected_rows = db_cusor.execute(command)

        if 0 == affected_rows:
            return {'error': "no such data!"}
        db_data = db_cusor.fetchone()
        user_amount = db_data[0]
        db_conn.close()

    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}

    return {'success': 1, 'game_issue': game_issue, 'game_result': game_result, 'user_bonus': user_amount}


@jsonrpc.method(name="get_lottery_opening_result_before_login")
def get_lottery_opening_result_before_login():
    """
       获取博彩合约上次的开奖结果(用户未登陆前)

       :param p_usr_sid:
       :return:
       """
    # if user_phone_check(p_usr_phone) == False:
    #     return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}
    db_conn = connect_db()
    #cannot connect to the db
    if db_conn == None:
        return {'error': "cannot connect to db!"}

    db_cusor = db_conn.cursor()

    try:

        # first, get the last game issue
        command = "select max(game_issue) from tbl_game_info"
        affected_rows = db_cusor.execute(command)
        if 0 == affected_rows:
            return {'error': "no such data!"}
        db_game_issue = db_cusor.fetchone()
        game_issue = db_game_issue[0] - 1

        command = "select game_result from tbl_game_info where game_issue= {}".format(game_issue)
        affected_rows = db_cusor.execute(command)
        if 0 == affected_rows:
            return {'error': "no such data!"}
        db_game_result = db_cusor.fetchone()
        game_result = db_game_result[0]

        db_conn.close()

    except MySQLdb.Error as err:
        return {'error': "mysql error: {}".format(err)}

    return {'success': 1, 'game_result': game_result}


#
# following rpc may not needed
#
# @jsonrpc.method(name="lottery_open")
# def lottery_open():
#     """
#     本轮游戏开奖
#
#     :return:
#     success: {'success': 1, [needed data]}
#     fail:    {'error': "error related info"}
#     """
#
#
# @jsonrpc.method(name="stop_then_start_game")
# def stop_then_start_game():
#     """
#     结束本轮游戏，并开启下一轮
#
#     :return:
#     success: {'success': 1, [needed data]}
#     fail:    {'error': "error related info"}
#     """
#
#
# @jsonrpc.method(name="get_user_history_bet_info")
# def get_user_history_bet_info(p_user_phone):
#     """
#     获取用户的历史投注信息
#
#     :param p_user_phone:
#     :return:
#     success: {'success': 1, 'data': 用户投注信息列表, [needed data]}
#     fail:    {'error': "error related info"}
#     """
#
#
# @jsonrpc.method(name="get_user_bet_info")
# def get_user_bet_info(p_user_phone):
#     """
#     获取用户上次的投注信息
#
#     :param p_user_phone:
#     :return:
#     success: {'success': 1, 'data': 用户投注信息, [needed data]}
#     fail:    {'error': "error related info"}
#     """
#
# @jsonrpc.method(name="get_user_bonus")
# def get_user_bonus(p_user_phone):
#     """
#     获取用户游戏的盈利
#
#     :param p_user_phone:
#     :return:
#     success: {'success': 1, 'user_bonus': bonus}1
#     fail:    {'error': "error related info"}
#     """
#     db_conn = connect_db()
#     #cannot connect to the db
#     if db_conn == None:
#         return {'error': "cannot connect to db!"}
#
#     db_cusor = db_conn.cursor()
#
#     command = "select sum(lottery_bonux) from tbl_lottery where user_phone={}".format(p_user_phone)
#     size = db_cusor.execute()
#
#     return {'success': 1, "user_bonus": []}
#
# @jsonrpc.method(name="get_user_winning_or_not")
# def get_user_winning_or_not(p_usr_phone):
#     """
#     获取用户是否中奖
#
#     :param p_user_phone:
#     :return:
#     success: {'success': 1, ‘win or not’: yes or no}
#     fail:    {'error': "error related info"}
#     """
#     if user_phone_check(p_usr_phone) == False:
#         return {'error': "user phone is illegal", 'rule': "should be numbers with length of 11, cannot start with 0"}
#
#     db_conn = connect_db()
#     #cannot connect to the db
#     if db_conn == None:
#         return {'error': "cannot connect to db!"}
#
#     db_cusor = db_conn.cursor()
#
#     # first, get the lottery result
#     command = "select lottery_result, lottery_number from tbl_lottery where game_issue=(select max(game_issue) from tbl_lottery) and user_phone={}".format(p_usr_phone)
#     affected_row = db_cusor.execute(command)
#
#     db_data = db_cusor.fetchall()
#
#     for data in db_data:
#         # print(data)
#         if data[0] == data[1]:
#             return {'success': 1, 'win or not': "yes"}
#
#     return {'success': 1, 'win or not': "no"}
#
#
#
#
# @jsonrpc.method(name="get_lottery_opening_result")
# def get_lottery_opening_result(p_usr_phone):
#     """
#     获取博彩合约上次的开奖结果
#
#     :return:
#     success: {'success': 1, 'data': [(lottery_issue, lottery_pond_amount, number_of_participants, total_participant_money,
#                                       lottery_start_time, result)]}
#     fail:    {'error': "error related info"}
#     """
#
#     if type(p_game_issue) != int:
#         return {'error': "game issue should be a number!"}
#
#     db_conn = connect_db()
#     #cannot connect to the db
#     if db_conn == None:
#         return {'error': "cannot connect to db!"}
#
#     db_cusor = db_conn.cursor()
#
#     command = "select game_issue, game_pot, number_of_participants, total_participant_money, create_time,\
#                game_result from tbl_game_info where game_issue={}".format(p_game_issue)
#
#     affected_row = db_cusor.execute(command)
#     db_lottery_opening_result = db_cusor.fetchone()
#
#     return {'success': 1, 'data': db_lottery_opening_result}
#
#
# @jsonrpc.method(name="get_rolling_windows_info")
# def get_rolling_windows_info(p_message_id=0, p_message_num=10):
#     """
#     获取滚动窗口所需的信息
#
#     :param: p_message_num
#     :return:
#     success: {'success': 1, 'data': 所需滚动信息}
#     fail:    {'error': "error related info"}
#     """
#     another_sess = app.open_session(request)
#     if type(p_message_id) != int:
#         return {'error': "message id should be a number!"}
#     if type(p_message_num) != int:
#         return {'error': "message num should be a number!"}
#
#     if p_message_id == 0:
#         another_sess['type'] = None
#
#     if  session.get('type') == None:
#         another_sess['type'] = 2
#
#     p_message_type = another_sess['type']
#     # print("p_message_type", p_message_type)
#
#     db_conn = connect_db()
#     #cannot connect to the db
#     if db_conn == None:
#         return {'error': "cannot connect to db!"}
#
#     db_cusor = db_conn.cursor()
#
#     try:# bonus info
#         if p_message_type == 2:
#             command = "select min(message_id), max(message_id) from tbl_message where game_issue=(select max(game_issue) from tbl_message where message_type=2) and message_type=2"
#         else:#bet info
#             command = "select min(message_id), max(message_id) from tbl_message where game_issue=(select max(game_issue) from tbl_game_info)"
#
#         affected_rows = db_cusor.execute(command)
#         db_message_id = db_cusor.fetchone()
#         global_start_message_id = db_message_id[0]
#         global_end_message_id = db_message_id[1]
#         if p_message_id == 0:
#             p_message_id = global_start_message_id
#         #print(global_start_message_id, global_end_message_id)
#
#
#         if p_message_type == 2:
#             #if 0, select  message from start in current game issue
#             command = "select message_id, message_value from tbl_message where game_issue=(select max(game_issue) from tbl_message  where message_type=2) and message_id>={} and message_type=2 limit {} ".format(p_message_id, p_message_num)
#         else:
#             command = "select message_id, message_value from tbl_message where game_issue=(select max(game_issue) from tbl_game_info) and message_id>={} limit {} ".format(p_message_id, p_message_num)
#         affected_rows = db_cusor.execute(command)
#
#         if 0 == affected_rows:
#             return {'error': "no such data!"}
#
#         db_data = []
#         db_message_id = p_message_id
#         for i in range(affected_rows):
#             each_row = db_cusor.fetchone()
#             db_message_id = each_row[0]
#             db_data.append(each_row[1])
#
#         db_message_id = db_message_id
#         if db_message_id == global_end_message_id:
#             if another_sess['type'] == 2:
#                 another_sess['type'] = 1
#                 p_message_type = another_sess['type']
#                 command = "select min(message_id), max(message_id) from tbl_message where game_issue=(select max(game_issue) from tbl_game_info)"
#                 affected_rows = db_cusor.execute(command)
#                 db_message_data = db_cusor.fetchone()
#                 db_message_id = db_message_data[0]
#                 if db_message_id == None:
#                     db_message_id = global_start_message_id
#                     another_sess['type'] = 2
#                     #print("from 2-1, none, from 1-2")
#                     #print("from 2-1")
#                     #print("1 start message id", db_message_id)
#
#             else:
#                 another_sess['type'] = 2
#                 p_message_type = another_sess['type']
#                 command = "select min(message_id), max(message_id) from tbl_message where game_issue=(select max(game_issue) from tbl_message where message_type=2) and message_type=2"
#                 affected_rows = db_cusor.execute(command)
#                 db_message_data = db_cusor.fetchone()
#                 db_message_id = db_message_data[0]
#                 if db_message_id == None:
#                     another_sess['type'] == 1
#                     db_message_id = global_start_message_id
#                     #print("from 1-2, none, from 2-1")
#                     #print("from 1-2")
#                     #print("1 start message id", db_message_id)
#
#
#
#
#
#     except MySQLdb.Error as err:
#         return {'error': "mysql error: {}".format(err)}
#
#
#     db_conn.commit()
#     db_conn.close()
#
#     return {'success': 1, 'message_id':db_message_id, 'data':db_data}

