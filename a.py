# -*- coding: utf-8 -*-
# import sys
# print sys.argv
#
# import getopt
# options, args = getopt.gnu_getopt(
#     # parameter,
#     sys.argv[1:],
#     'fi',
#     ['full',
#      'incremental',
#      'all-databases',
#      'database=',
#      'time=',
#      'date=',
#      'quiet']
# )
# print args
# for o,a in options:
#     print o ,a
#
#
#
# import os
# import glob
#
# os.chdir('/path/to/127000000001_3306/backmanage_mysql_t/full/')
# print os.path.abspath(os.curdir)
# os.path.isfile('27000000001_3306_[backmanage_mysql_t]_full_20180205*')
# print glob.glob('a[432].sql')
#
# import binascii
# print ord('[')
#
# print chr(91)


import os,pymssql,json
from os import getenv
os.environ['PYMSSQL_TEST_SERVER'] = '192.168.134.1'
os.environ['PYMSSQL_TEST_USERNAME'] = 'u1ge_add_item'
os.environ['PYMSSQL_TEST_PASSWORD'] = 'u1ge_add_item123'
server = getenv("PYMSSQL_TEST_SERVER")
user = getenv("PYMSSQL_TEST_USERNAME")
password = getenv("PYMSSQL_TEST_PASSWORD")

accounts = ["邻家药铺","啊吧唧","行云流玛","惠子测试","韦小宝","抚琴笑沧桑","叼丶样","丶"]
items = [[3214, 44], [43432, 32], [43432, 32], [43432, 32], [43432, 32], [43432, 32], [43432, 32]]
print server, user, password
with pymssql.connect(server, user, password, "pcik_15_char") as conn:
    with conn.cursor(as_dict=True) as cursor:
        cursor.callproc('p_u1ge_add_item', (json.dumps(accounts,ensure_ascii=False), json.dumps(items),))
        for row in cursor:
           print row['reason'],row['charname']



import datetime
startdate = datetime.datetime.strftime(datetime.datetime.now() ,'%Y-%m-%d')
enddate = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1),'%Y-%m-%d')
with pymssql.connect(server, user, password, "pcik_15_char") as conn:
    with conn.cursor(as_dict=True) as cursor:
        cursor.callproc('p_get_u1ge_additem_log', (startdate,enddate,))
        for row in cursor:
            print row['reason'], row['charname']