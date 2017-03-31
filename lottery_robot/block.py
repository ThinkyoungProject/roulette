#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


import json
from utility import to_utf8, to_localtime_str


class BlockInfo(object):
    def __init__(self):
        # 块hash
        self.block_id = ''
        # 块高度
        self.block_num = 0
        # 块大小
        self.block_size = 0
        # 上个块的块hash
        self.previous = ''
        # 块中交易信息摘要
        self.trx_digest = ''
        # 代理上轮出块secret
        self.prev_secret = ''
        # 代理本轮出块secret hash
        self.next_secret_hash = ''
        # 随机种子
        self.random_seed = ''
        # 出块代理
        self.signee = ''
        # 出块时间
        self.block_time = ''
        # 块中交易
        self.transactions = []
        # 块中交易总数量
        self.trx_count = 0
        # 块中交易总金额
        self.trx_amount = 0
        # 块中手续费总金额
        self.trx_fee = 0


    def from_block_resp(self, block_resp, block_signee_resp):
        block_result = json.loads(block_resp).get("result")
        self.block_id = to_utf8(block_result.get("id"))
        self.block_num = block_result.get("block_num")
        self.block_size = block_result.get("block_size")
        self.previous = to_utf8(block_result.get("previous"))
        self.trx_digest = to_utf8(block_result.get("transaction_digest"))
        self.prev_secret = to_utf8(block_result.get("previous_secret"))
        self.next_secret_hash = to_utf8(block_result.get("next_secret_hash"))
        self.random_seed = to_utf8(block_result.get("random_seed"))
        self.block_time = to_localtime_str(to_utf8(block_result.get("timestamp")))
        self.transactions = block_result.get("user_transaction_ids")
        self.trx_count = len(self.transactions)
        self.signee = to_utf8(json.loads(block_signee_resp).get("result"))
