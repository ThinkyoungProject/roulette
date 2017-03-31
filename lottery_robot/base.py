#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'

#######################交易类型########################
#账户相关
#普通转账
TRX_TYPE_TRANSFER = 0
#代理领工资
TRX_TYPE_WITHDRAW_PAY = 1
#注册账户
TRX_TYPE_REGISTER_ACCOUNT = 2
#注册代理
TRX_TYPE_UPDATE_ACCOUNT = 3

#合约相关
#注册合约
TRX_TYPE_REGISTER_CONTRACT = 10
#合约充值
TRX_TYPE_DEPOSIT_CONTRACT = 11
#合约升级
TRX_TYPE_UPGRADE_CONTRACT = 12
#合约销毁
TRX_TYPE_DESTROY_CONTRACT = 13
#调用合约
TRX_TYPE_CALL_CONTRACT = 14


#######################合约状态##########################
DESTROY_STATE = 0
TEMP_STATE = 1
FOREVER_STATE = 2