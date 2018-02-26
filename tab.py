# # # #cat tab.py
# # # #!/usr/bin/env python
# # # # python startup file
# # # import sys
# # # import readline
# # # import rlcompleter
# # # import atexit
# # # import os
# # # # tab completion
import os,django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','adminset.settings')
django.setup()
from dbmanage.myapp.models import Db_instance,Db_name,Db_account
from cmdb.models import Host,HostGroup
from dbmanage.myapp.include.mon import *
from dbmanage.myapp.include.scheduled import *
# a=mon_mysql()
# table_check()
# # #
# # #
# # # a=Db_instance(ip='192.168.134.130',port='3308')
# # # a.save()
# # # print(a)
# # #
# # #
# # # # db_instance = Db_instance.objects.filter()
# # # #
# # # # d = db_instance.filter(db_account__user__isnull=False).values('port','db_account__user','db_account__db_account_role')
# # # #
# # # # print(d[0]['port'])
# #
# # a={u'172.17.0.2': [(11, u'3306', u'normal_account', u'all'), (11, u'3306', u'admin_account', u'all'), (8, u'9658', u'normal_account', u'all'), (8, u'9658', u'normal_account', u'all'), (6, u'69559', None, None), (7, u'9859', None, None), (5, u'9888', None, None)], u'192.134.26.15': [(15, u'3306', None, None)], u'192.168.0.13': [(2, u'6589', None, None)]}
# #
# # h={}
# # for k,v in a.items():
# #     for port_account in v:
# #
# #         if h.has_key(port_account[0]):
# #             h[port_account[0]][k + ':' + port_account[1]].append([port_account[2], port_account[3]])
# #         else:
# #             h[port_account[0]]={}
# #             h[port_account[0]][k + ':' + port_account[1]]=[]
# #             h[port_account[0]][k + ':' + port_account[1]].append([port_account[2], port_account[3]])
# # print h
#
# import time,hmac,base64
#
# def generate_token(key, expire=3600):
#
#     ts_str = str(time.time() + expire)
#     ts_byte = ts_str.encode("utf-8")
#     print(type(ts_byte))
#     sha1_tshexstr  = hmac.new(key.encode("utf-8"),ts_byte).hexdigest()
#     token = ts_str+':'+sha1_tshexstr
#     b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
#     return b64_token.decode("utf-8")
#
#
#
# # MTUxMzA2NzUzOS41OToxZDdkOWI1ZTQ1ZWRlNzM0YzliZjhhNmJkZTNlMTNkMg==
# # MTUxMzA2NzU1OS4yNDo5NmE3ZmU0NDFlYzE5MDA5ODY1ZjIxMzE0ZTJlMmVjMQ==

#
# def f():
#     e = 'Duplicate key!'
#     return ([str(e)], ''), ['error']
#
#
# d,k= f()
# print d[0],k[0]
#
#
#
#
# d = {'d':321}
# import json
# print json.dumps(d)

def d():
    a()
def a():
    print 1

def b():
    print 2

d()