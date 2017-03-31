#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


import json

import time
from transaction import TransactionInfo
from collect_config import RPC_SERVER_IP, RPC_SERVER_PORT, RPC_USER, RPC_PASS
from rpc_client import rpc_socket
from utility import to_utf8

block_sql_tpl = '''insert into tbl_block(block_id, block_num, block_size, previous, trx_digest, prev_secret, '''\
    ''' next_secret_hash, random_seed, signee, block_time, trans_num, trans_amount) ''' \
    ''' values("%s", %d, %d, "%s", "%s", "%s", "%s", "%s","%s", "%s", %d, %d)'''

trx_sql_tpl = '''insert into tbl_transaction(trx_id, block_id, block_num, block_position, trx_type, from_acct, '''\
    ''' from_addr, to_acct, to_addr, amount, fee, memo, trx_time, is_completed) ''' \
    ''' values("%s", "%s", %d, %d, %d, "%s", "%s", "%s", "%s", %d, %d, "%s", "%s", 0)'''

contract_trx_sql_tpl = '''insert into tbl_transaction(trx_id, block_id, block_num, block_position, trx_type, '''\
    '''from_acct, from_addr, to_acct, to_addr, amount, fee, memo, ''' \
    ''' trx_time, called_abi, abi_params, extra_trx_id, is_completed) values("%s", "%s", %d, %d, %d, "%s", ''' \
    ''' "%s", "%s", "%s", %d, %d, "%s", "%s", "%s", "%s", "%s", %d)'''

contract_extra_trx_sql_tpl = '''insert into tbl_transaction_ex(trx_id, orig_trx_id, from_acct, from_addr, '''\
    ''' to_acct, to_addr, amount, fee, memo, trx_time) ''' \
    ''' values("%s", "%s", "%s", "%s", "%s", "%s", %d, %d, "%s", "%s") '''

def get_block_time(rpc,blocknum):
    blockresp = rpc.rpc_request('blockchain_get_block',[str(blocknum)])
    block = json.loads(blockresp).get('result')
    if block is None :
        return ''
    tmsz = block.get('timestamp')
    tm=time.strptime(tmsz,'%Y-%m-%dT%X')
    timeStamp = int(time.mktime(tm))
    timeStamp+=8*3600
    ret=time.localtime(timeStamp)
    return time.strftime("%Y-%m-%d %H:%M:%S",ret)
def collect_block(rpc,from_block,to_block,caller_pub,db_pool) :
    for i in range(from_block,to_block+1):
        blockresp = rpc.rpc_request('blockchain_get_block',[str(i)])
        block = json.loads(blockresp).get('result')
        user_trx_ids = block.get('user_transaction_ids')
        for id in user_trx_ids :
            ret =  is_contract_trx(rpc, id)
            if ret == False :
                continue
            contract_trx_rsp =  rpc.rpc_request('blockchain_get_transaction',[id])
            contract_trx = json.loads(contract_trx_rsp).get('result')[1]
            if contract_trx.get('trx').get('operations')[0].get('data').get('trx').\
                                  get('operations')[0].get('type') != 'call_contract_op_type' :
                continue
            if contract_trx.get('trx').get('operations')[0].get('data').get('trx').\
                                  get('operations')[0].get('data').get('caller') != caller_pub :
                continue

            trx = TransactionInfo()
            trx.from_contract_trx_operation_resp(json.loads(contract_trx_rsp).get('result'))
            for op in trx.event_operations :
                op.from_event_operation(db_pool)

def get_rpc_connection():
    rpc = rpc_socket()
    rpc.connection_made(RPC_SERVER_IP,RPC_SERVER_PORT)
    return rpc


def rpc_login(rpc):
    login_resp = rpc.rpc_request("login", [RPC_USER, RPC_PASS])
    if json.loads(login_resp).get("result") is None:
        raise Exception("rpc login error")

def get_block_count(rpc):
    block_count_resp = rpc.rpc_request('blockchain_get_block_count', [])
    if json.loads(block_count_resp).get("result") is None:
        raise Exception("blockchain_get_block_count error")
    return block_count_resp

def get_trx_result_id(rpc,trx):
    result = rpc.rpc_request('get_result_trx_id', [trx.trx_id])
    if json.loads(result).get('result') is None :
        return False
    trx.result_trx_id = json.loads(result).get('result')
    return True

def execute_contract(rpc,db_pool,command) :
    contract_resp = rpc.rpc_request('call_contract',command.split(' '))
    if json.loads(contract_resp).get('result') is None:
        print 'pls check', contract_resp
        raise  Exception('call contract error')
    contract_trx_info = TransactionInfo()
    contract_trx_info.from_contract_trx_resp(rpc,contract_resp)
    return contract_trx_info

def update_block_trx_amount(db_pool, block_info):
    sql = '''update tbl_block set trans_amount = %d, trans_fee = %d where block_id = "%s" ''' \
          % (block_info.trx_amount, block_info.trx_fee, block_info.block_id)
    db_pool.execute(sql)

def is_contract_trx(rpc, trx_id):
    trx_resp = rpc.rpc_request("blockchain_get_transaction", [trx_id])
    if json.loads(trx_resp).get("result") is None:
        raise Exception("blockchain_get_transaction error")
    first_op_type = to_utf8(json.loads(trx_resp).get("result")[1].get("trx").get("operations")[0].get("type"))
    if first_op_type == "transaction_op_type":
        return True
    return False


def collect_contract_transaction(rpc, db_pool, trx_id):
    contrac_trx_resp= rpc.rpc_request("blockchain_get_transaction", [trx_id])

    if json.loads(contrac_trx_resp).get("result") is None:
        return False
    contract_trx_info = TransactionInfo()
    contract_trx_info.from_contract_trx_operation_resp(json.loads(contrac_trx_resp).get("result"))
    return contract_trx_info

