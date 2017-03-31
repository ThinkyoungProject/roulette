#!/usr/bin/env python
# encoding=utf8

__author__ = 'hasee'

######################################################################
#  数据处理逻辑：
#  1. 先从数据库中获取出上次采集已成功提交的区块号
#  2. 采集前清理掉超出此区块号的tbl_block, tbl_transaction, tbl_transaction_ex, tbl_contract_info表中相关记录
#  3. 考虑到对同一个合约的操作，可能会有并发问题导致的合约操作的先后顺序颠倒的问题，
#       对于tbl_contract_info表，采用replace into ON DUPLICATE的方式
#  4. 对于tbl_contract_abi, tbl_contract_storage, tbl_contract_event表，在遇到注册相关合约相关的交易的处理上，
#       先清理，再插入
######################################################################
import json,traceback
import rpc_biz
from time import sleep,strftime,localtime
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import transaction
current_game_issue = 0
current_game_target_block = 0
sync_end_per_round = 0
global_trx_id = []
global_trx_for_open = None
update_state_for_tbl_game_info = '''update tbl_game_info set game_state=%d where game_issue=%d'''
get_bids_info_tbl_lottery_info = '''select id,user_phone,lottery_number,lottery_amount from tbl_lottery'''\
                                 ''' where game_issue=%d '''
trx_sql_tpl = '''insert into tbl_transaction(trx_id, transfer_from_address, transfer_to_address,'''\
              '''transfer_amount,block_num,block_trx_num,transfer_fee,trx_type,trx_state,game_issue,create_time)'''\
             ''' values('%s','%s','%s',%d,%d,%d,%d,%d,%d,%d,'%s')'''
insert_game_info_tbl = '''insert into tbl_game_info (game_issue,game_pot,target_block_num,number_of_participants,total_participant_money,game_result,game_state,create_time)'''\
    '''value(%d,%f,%d,%d,%f,%d,%d,'%s') '''
game_sql_pot_time_tbl='''update tbl_game_info set create_time='%s' ,game_pot=%d '''\
    '''where game_issue=%d '''


#合约的调用命令，contract address写死
call_contract = '''CONK6nJEJzSMp8TLjWMpTGFXCisL2akeUiUV test0 %s %s ALP 1 '''
caller_address = 'ALP2Atktj74dKJUZuRuuLux6hjpQscuDYnzf'
caller_public = 'ALP7k1zQEVNpRC7PTpBmURgrW4Tjg1ogxsUcMaVwp6xK6qVFojSVs'

def update_tbl_message(current_issue,db_pool):
    if current_issue <= 0 :
        return
    db_pool.execute('SELECT DISTINCT(user_phone),SUM(lottery_bonus) from tbl_lottery where game_issue=%d GROUP BY user_phone'%current_issue)
    user_info = db_pool.fetchall()
    db_user_create_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for i in user_info :
        user = i[0]
        if i[1] is None:
            continue
        bonus = int(i[1])
        if bonus == 0:
            continue
        #修改message ，按照user|bonus进行存储
        db_pool.execute('''select user_name from tbl_user where user_phone='%s' '''%user)
        ret = db_pool.fetchone()
        if ret is not None:
            user=ret[0]
        messagesz='恭喜'+user+'获得了'+str(bonus)+'元宝'
        db_pool.execute('''insert into tbl_message(message_type,message_value,create_time,game_issue) values(%d,'%s','%s',%d)'''\
                            %(2,messagesz.encode('utf8'),db_user_create_time,current_issue))
        db_pool.execute('''insert into tbl_rolling_message(message_value,game_issue) values('%s',%d)'''\
                            %(messagesz.encode('utf8'),current_issue))
        db_pool.execute('''delete from tbl_rolling_message where game_issue>0 and game_issue < %d '''%current_issue)
    return

def synchronous(rpc,db_pool):
    global current_game_issue
    global global_trx_for_open
    latest_block_num =  get_latest_block_num(rpc)
    db_pool.execute('''select game_issue,target_block_num,game_result from tbl_game_info where game_state='3' order by game_issue desc limit 1 ''')
    record = db_pool.fetchone()
    db_user_create_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    if record is None :
        current_game_issue=1
        trx = rpc_biz.execute_contract(rpc,db_pool,call_contract % ('game_create',str(current_game_issue)))
        trx.trx_type = 0
        global_trx_for_open=trx
        sql = trx_sql_tpl % (trx.trx_id,trx.transfer_from_address,trx.transfer_to_address\
                                             ,trx.transfer_amount,trx.block_num,trx.block_trx_num,trx.transfer_fee,trx.trx_type\
                                             ,trx.trx_state,current_game_issue,db_user_create_time)
        db_pool.execute(sql)
        #db_pool.runquery(sql)
        return True
    current_game_issue = record[0]
    current_game_target_block = record[1]
    game_result = record[2]
    ret =  clear_last_garbage_data(current_game_issue,current_game_target_block,game_result,db_pool)
    if current_game_issue != ret :
         rpc_biz.collect_block(rpc,current_game_target_block+1,latest_block_num,caller_public,db_pool)
         db_pool.execute('''select game_issue,target_block_num,game_result from tbl_game_info  order by game_issue desc limit 1 ''')
         record=db_pool.fetchone()
         current_game_issue=record[0]
         current_game_target_block=record[1]
    else:
        return
    trx = rpc_biz.execute_contract(rpc,db_pool,call_contract % ('game_end',str(current_game_issue+1)+'|1'))
    trx.trx_type = 2
    global_trx_for_open=trx
    current_game_issue+=1

    sql = trx_sql_tpl % (trx.trx_id,trx.transfer_from_address,trx.transfer_to_address\
                                             ,trx.transfer_amount,trx.block_num,trx.block_trx_num,trx.transfer_fee,trx.trx_type\
                                           ,trx.trx_state,current_game_issue,db_user_create_time)
    print db_pool.execute(sql)
    return True

def execute(record,issue,function,rpc,db_pool) :
    global global_trx_id
    print 'game join begin'
    command=str(issue)
    type=-1
    if function == 'game_join' :
        type=1
    print 'record is ',record
    for item in record :
        orderid = item[0]
        userid = item[1]
        lottery_num = item[2]
        lottery_account = item[3]
        param = '|%s,%s,%s,%s'%(userid,lottery_account,lottery_num,orderid)
        if len( command + param ) > 1000 :
            trx= rpc_biz.execute_contract(rpc,db_pool,call_contract % (function,command))
            global_trx_id.append(trx)
            trx.game_issue = issue
            trx.trx_type = type
            command = str(issue)
        else:
            command+=param
    if command != str(issue) :
        trx=  rpc_biz.execute_contract(rpc,db_pool,call_contract % (function,command))
        trx.game_issue = issue
        trx.trx_type = type
        global_trx_id.append(trx)
        command = str(issue)
    db_user_create_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    for trx in global_trx_id :
        sql = trx_sql_tpl % (trx.trx_id,trx.transfer_from_address,trx.transfer_to_address\
                       ,trx.transfer_amount,trx.block_num,trx.block_trx_num,trx.transfer_fee,trx.trx_type\
                      ,trx.trx_state,current_game_issue,db_user_create_time)
        db_pool.execute(sql)

def execute_record(record,rpc,function,issue,db_pool):
    execute(record,issue,function,rpc, db_pool)

def do_collect_app(conn):
    db_pool = conn.cursor()
    global current_game_issue
    global current_game_target_block
    global global_trx_id
    global global_trx_for_open
    try:
        rpc_cli = rpc_biz.get_rpc_connection()
        rpc_biz.rpc_login(rpc_cli)
        # 程序启动，设置为同步状态
        synchronous(rpc_cli,db_pool)
        conn.commit()
        need_to_wait = False
        #
        #latest_block_num = yield get_latest_block_num()
        # 获取当前链上最新块号
        while True:
            sleep(1)
            #获取当前最新块号
            latest_block_num = get_latest_block_num(rpc_cli)
            conn.commit()
            #等待game_create_event
            if global_trx_for_open is not None :
                trx = global_trx_for_open
                ret = rpc_biz.get_trx_result_id(rpc_cli,trx)
                if ret == False:
                    continue
                trx.from_constract_trx_cofirm_resp(rpc_cli,db_pool)
                rpc_biz.collect_contract_transaction(rpc_cli, db_pool, trx.result_trx_id)
                for op in trx.event_operations :
                    op.from_event_operation(db_pool)
                global_trx_for_open = None
                db_pool.execute('select game_issue,target_block_num from tbl_game_info order by game_issue desc limit 1 ')
                record = db_pool.fetchone()
                current_game_target_block = int(record[1])
                update_tbl_message(current_game_issue-1,db_pool)
                db_pool.execute('select game_pot from tbl_game_info where game_state=3 order by game_issue desc limit 1 ')
                r_pot =db_pool.fetchone()
                pot=0
                if r_pot is not None:
                    pot = int(r_pot[0])
                print 'haha',pot,current_game_issue,latest_block_num
                db_user_create_time=rpc_biz.get_block_time(rpc_cli,latest_block_num)
                sql =  game_sql_pot_time_tbl% (db_user_create_time,pot,current_game_issue)
                db_pool.execute(sql)
            conn.commit()

            print 'current_game_target_block',current_game_target_block,latest_block_num
            if current_game_target_block -1 == latest_block_num :
                #修改投注状态
                db_pool.execute('select game_state from tbl_game_info where game_issue=%d'%current_game_issue)
                state=db_pool.fetchone()[0]
                if state != 0 :
                    continue
                sql =  update_state_for_tbl_game_info % (1,current_game_issue)
                db_pool.execute(sql)
                conn.commit()
                #在投注信息表中获取当前game_issue下的所有交易
                sql = get_bids_info_tbl_lottery_info % (current_game_issue)
                db_pool.execute(sql)
                record = db_pool.fetchall()
                execute_record(record,rpc_cli,'game_join',current_game_issue,db_pool)
                #修改tbl_game_info中的是信息
                db_pool.execute('select count(user_phone) from tbl_lottery where game_issue = %s' %current_game_issue)
                particapte_num = db_pool.fetchone()
                db_pool.execute('select sum(lottery_amount) from tbl_lottery where game_issue = %s' %current_game_issue)
                revenue = db_pool.fetchone()
                if particapte_num[0] is None or revenue[0] is None :
                    continue
                print particapte_num[0],revenue[0]
                db_pool.execute('''update tbl_game_info set number_of_participants=%d , total_participant_money=%d '''\
                        '''where game_issue=%d ''' %(particapte_num[0],revenue[0],current_game_issue))
            #验证当前交易是否都已经admit
            elif current_game_target_block  == latest_block_num :
                for trx in global_trx_id :
                    ret = rpc_biz.get_trx_result_id(rpc_cli,trx)
                    if ret == False :
                        need_to_wait = True
                        break
                    trx.from_constract_trx_cofirm_resp(rpc_cli,db_pool)
                    temp = rpc_biz.collect_contract_transaction(rpc_cli, db_pool, trx.result_trx_id)
                    for op in temp.event_operations :
                        op.from_event_operation(db_pool)
                if need_to_wait == False :
                    #执行game_end
                    trx= rpc_biz.execute_contract(rpc_cli,db_pool,call_contract % ('game_end',str(current_game_issue+1)+'|1'))
                    current_game_issue+=1
                    global_trx_id = []
                    trx.trx_type = 2
                    trx.game_issue=current_game_issue
                    global_trx_for_open = trx
                    db_user_create_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
                    sql = trx_sql_tpl % (trx.trx_id,trx.transfer_from_address,trx.transfer_to_address\
                                             ,trx.transfer_amount,trx.block_num,trx.block_trx_num,trx.transfer_fee,trx.trx_type\
                                           ,trx.trx_state,current_game_issue,db_user_create_time)
                    db_pool.execute(sql)
                else:
                    db_pool.execute('select game_state from tbl_game_info where game_issue=%d'%current_game_issue)
                    state=db_pool.fetchone()[0]
                    if state == 2 :
                        continue
                    sql = update_state_for_tbl_game_info %(2,current_game_issue)
                    db_pool.execute(sql)
            # 是否调用game_end
            elif current_game_target_block < latest_block_num :
                for trx in global_trx_id :
                    ret = rpc_biz.get_trx_result_id(rpc_cli,trx)
                    if ret == False :
                        continue
                    trx.from_constract_trx_cofirm_resp(rpc_cli,db_pool)
                    temp = rpc_biz.collect_contract_transaction(rpc_cli, db_pool, trx.result_trx_id)
                    for op in temp.event_operations :
                        op.from_event_operation(db_pool)
                    #创建新的游戏期数
                trx= rpc_biz.execute_contract(rpc_cli,db_pool,call_contract % ('game_end',str(current_game_issue+1)+'|2'))
                global_trx_id = []
                current_game_issue+=1
                trx.trx_type = 2
                trx.game_issue=current_game_issue
                global_trx_for_open = trx
                db_user_create_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
                sql = trx_sql_tpl % (trx.trx_id,trx.transfer_from_address,trx.transfer_to_address\
                                             ,trx.transfer_amount,trx.block_num,trx.block_trx_num,trx.transfer_fee,trx.trx_type\
                                           ,trx.trx_state,current_game_issue,db_user_create_time)
                db_pool.execute(sql)
                need_to_wait = False
    except Exception, ex:
        traceback.print_exc()
        return

def clear_last_garbage_data(issue,target_block,result,db_pool):
    #db_pool.execute('''delete from tbl_transaction where game_issue>%d''' %issue)
    db_pool.execute('''select game_issue,target_block_num from tbl_game_info order by game_issue desc limit 1 ''')
    record = db_pool.fetchone()
    game_issue = record[1]
    if game_issue == issue :
        return issue
    return game_issue

def get_latest_block_num(rpc):
    block_count_resp =  rpc_biz.get_block_count(rpc)
    return  json.loads(block_count_resp).get("result")