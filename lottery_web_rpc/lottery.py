# lottery.py
# Author: wengqiang
# Date Last Modified: 10:14 2017/2/22
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


from lottery_web_rpc import app, handler
import datetime
import logging

if __name__ == "__main__":
    app.secret_key = "any random string"
    # app.config['SESSION_COOKIE_NAME'] = 'lottery_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    # app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    # app.permanent_session_lifetime = datetime.timedelta(hours=24)
    # sess.init_app(app)

    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host="0.0.0.0", port=51888)







