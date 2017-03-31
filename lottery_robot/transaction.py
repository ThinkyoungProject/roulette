#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


import json
import time
from base import TRX_TYPE_CALL_CONTRACT
from utility import to_utf8, to_localtime_str
import sys
reload(sys)
sys.setdefaultencoding('utf8')

user_sql_tbl = '''update  tbl_user set user_balance=%f '''\
    '''where user_phone='%s' '''

lottery_sql_state_tbl= '''update tbl_lottery set lottery_state=%d '''\
    '''where id=%d and user_phone='%s' '''

lottery_sql_bonus_tbl= '''update tbl_lottery set lottery_result=%d ,lottery_bonus=%f '''\
    '''where id=%d and user_phone='%s' '''


game_sql_tbl_for_state = '''update tbl_game_info set game_state = %d ''' \
    '''where game_issue=%s '''
game_sql_tbl= '''update tbl_game_info set game_result=%d,game_pot=%d '''\
    '''where game_issue=%d '''
update_tbl_transacton_for_confirm = '''update tbl_transaction set block_id ='%s' ,block_num=%d,block_trx_num =%d '''\
   '''where result_trx_id ='%s' '''
insert_game_info_tbl = '''insert into tbl_game_info (game_issue,target_block_num,number_of_participants,total_participant_money,game_result,game_state)'''\
    '''value(%d,%d,%d,%f,%d,%d) '''

#transaction_sql_tbl


class TransactionInfo(object):
    def __init__(self):
        #record id
        self.game_issue = 0
        #transaction id
        self.trx_id = ''
        #transaction result id
        self.result_trx_id = ''
        #transfer source address
        self.transfer_from_address = ''
        #transfer destnation address
        self.transfer_to_address = ''
        #transfer amount
        self.transfer_amount = 0
        self.block_id = ' '
        self.block_num = 0
        self.block_trx_num = 0
        self.transfer_fee = 0
        #the type of transaction: 0 :create game,1;bid 2:open
        self.trx_type = 0
        #the state fo trx 0:not admit 1:admit
        self.trx_state = 0
        #transaction operations of event
        self.event_operations=[]

    def from_constract_trx_cofirm_resp(self,rpc,db_pool):
        contract_trx_resp = json.loads(rpc.rpc_request('blockchain_get_transaction',[self.result_trx_id])).get('result')

        if contract_trx_resp == None :
            return False
        db_pool.execute("update tbl_transaction set result_trx_id='%s',trx_state=%d where trx_id='%s' "%(self.result_trx_id,1,self.trx_id))
        self.from_contract_trx_operation_resp(contract_trx_resp)
        contract_trx_resp = contract_trx_resp[1]
        self.trx_state = 1
        self.block_id = ''
        self.block_num = contract_trx_resp.get('chain_location').get('block_num')
        self.block_trx_num = contract_trx_resp.get('chain_location').get('trx_num')
        self.block_id = json.loads(rpc.rpc_request('blockchain_get_block',[str(self.block_num)])).get('result').get('id')
        print self.block_id,self.block_num,self.block_trx_num,self.result_trx_id
        sql = update_tbl_transacton_for_confirm %(self.block_id,self.block_num,self.block_trx_num,self.result_trx_id)
        db_pool.execute(sql)
        return True

    def from_contract_trx_resp(self,rpc,contract_execute_result_resp):
        contract_execute_result = json.loads((contract_execute_result_resp)).get("result")
        self.trx_id = contract_execute_result.get('entry_id')
        self.transfer_from_address = 'ALP2Atktj74dKJUZuRuuLux6hjpQscuDYnzf'
        self.transfer_to_address = contract_execute_result.get('trx').get('operations')[0].get('data').get('contract')
        self.transfer_fee = contract_execute_result.get('fee').get('amount')
        self.trx_state = contract_execute_result.get('is_confirmed')
        #self.result_trx_id =  json.loads(rpc.rpc_request("get_result_trx_id", [self.trx_id])).get('result')
        #self.from_contract_trx_operation_resp(contract_execute_result_resp)

    def from_contract_trx_operation_resp(self, contract_trx_resp):
        contract_trx_result = contract_trx_resp[1]
        operations=contract_trx_result.get('trx').get("operations")
        for op in operations :
            if op.get("type") == "event_op_type" :
                data=op.get("data")
                operation=EventOperationInfo()
                operation.id=data.get("id")
                operation.type = "event_op_type"
                operation.event_type = data.get("event_type")
                operation.event_param = data.get("event_param")
                operation.is_truncated = data.get("is_truncated")=='true'
                self.event_operations.append(operation)

class EventOperationInfo(object):
    def __init__(self):
        self.type = ''
        self.id = ''
        self.event_type = ''
        self.event_param = ''
        self.is_truncated = False

    def from_event_operation(self,db_pool):
        result=dict()
        if self.type == 'envent_op_type' :
            return False
        if self.event_type == 'game_create_event':
            #target_block_num = int(self.event_param)
            ret=self.event_param.strip().split(',')
            result['game_issue']=int(ret[0])
            result['target_block_num'] = int(ret[1])
            try:
                sql = insert_game_info_tbl % (result['game_issue'],result['target_block_num'],0,0,0,0)
                db_pool.execute(sql)
            except:
                pass
            return True
        elif self.event_type == 'account_bid_event':
            account_bid=self.event_param
            ret=account_bid.strip().split(',')
            result['user_id'] = ret[0]
            result['lottery_amount'] = float(ret[1])
            result['id'] = int(ret[2])
            result['user_balance'] = float(ret[3])
            sql = lottery_sql_state_tbl % (1,result['id'],result['user_id'])
            db_pool.execute(sql)
            sql = user_sql_tbl % (result['user_balance'],result['user_id'])
            db_pool.execute(sql)
            return (True)
        elif self.event_type == 'award_deliver_event':
            award_deliver = self.event_param
            ret=award_deliver.strip().split(',')
            result['user_id'] = ret[0]
            result['user_balance'] = float(ret[1])
            result['lottery_bonus'] = float(ret[2])
            result['id'] =int( ret[3])
            sql = user_sql_tbl % (result['user_balance'],result['user_id'])
            print sql
            db_pool.execute(sql)
            sql = lottery_sql_bonus_tbl % (1,result['lottery_bonus'],result['id'],result['user_id'])
            db_pool.execute(sql)

            #修改message ，按照user|bonus进行存储
            messagesz='恭喜'+result['user_id']+'获得了'+str(result['lottery_bonus'])+'元宝'
            db_user_create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            #db_pool.execute('''insert into tbl_message(message_type,message_value,create_time,game_issue)'''\
            #                '''select %d as message_type,'%s' as message_value,'%s'as create_time,game_issue from tbl_lottery where id=%d'''\
            #                   %(2,messagesz.encode('utf8'),db_user_create_time,result['id']))

            return True
        elif self.event_type == 'end_game_event':
            game_result = self.event_param
            ret=game_result.strip().split(',')
            result['game_issue'] = int(ret[0])
            result['game_result'] = int(ret[1])
            result['game_pot'] = int(ret[2])
            global_game_pot = result['game_pot']
            sql = game_sql_tbl % (result['game_result'] , result['game_pot'] ,result['game_issue'])
            db_pool.execute(sql)
            sql = game_sql_tbl_for_state%(3,result['game_issue'])
            db_pool.execute(sql)
            db_pool.execute('''delete from tbl_rolling_message where game_issue=0 ''')
            return True
        return False
