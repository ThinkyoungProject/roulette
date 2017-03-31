# coding:UTF-8
__author__ = 'Administrator'

from collect_config import DB_IP,DB_USER,DB_PASS,DB_PORT,DB_NAME,LOG_FILENAME,LOG_LEVEL
from collect_data import do_collect_app
import MySQLdb
import  logging,time

if __name__ == '__main__':
    LOG_FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(message)s'
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, filename=LOG_FILENAME, filenode="a")

    conn = MySQLdb.connect(host=DB_IP, user=DB_USER, passwd=DB_PASS, port=DB_PORT, db=DB_NAME,charset='utf8')
    #cur = conn.cursor()
    do_collect_app(conn)
    conn.commit()
    conn.close()

