# coding: UTF-8
import utility
import logging
import time
import datetime
import sys
import math
reload(sys)
sys.setdefaultencoding('utf-8')



class luckywheel(utility.PluginBase):
    def __init__(self):
        super(luckywheel,self).__init__()
        self.email_group = 'lottery_web_rpc'
        self.table=''
        self.previous_record = None
        self.subject = '幸运大转盘'
    def handle_notify(self):
        sql_str = 'select game_issue,target_block_num,game_state from tbl_game_info order by game_issue desc limit 1'
        record = self.manager.db.my_query_one_line(sql_str)
        if self.previous_record is None:
            self.previous_record=record
            return
        if 0 != cmp(record,self.previous_record) :
            self.previous_record=record
            return
        warning_content='lucky_wheel合约数据库已经超过1min中没有发生变化，请检查'
        self.manager.mailer.send_email(self.email_group, self.subject+"预警", content=warning_content)

    def run(self):
        super(luckywheel,self).run()
        self.handle_notify()
