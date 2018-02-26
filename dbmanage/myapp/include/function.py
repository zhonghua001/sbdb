#!/bin/env python
# -*- coding:utf-8 -*-
import MySQLdb
import commands
import datetime
import os
import sys
from django.contrib.auth.models import  Group
from django.conf import settings
from dbmanage.myapp.include.encrypt import prpcrypt
from cmdb.models import Host,HostGroup
from dbmanage.myapp.models import Db_name, Db_account, Oper_log, Login_log, Db_group,Db_database_permission_detail,Db_database_permission,Db_instance,Instance_account_admin
from accounts.models import UserInfo
from django.http import JsonResponse,HttpResponse
# from dbmanage.mypro import settings
from django.conf import settings
from django.utils import timezone
import pytz
import json
import time
import base64
import hmac

#
# def get_item(data_dict,item):
#     try:
#        item_value = data_dict[item]
#        return item_value
#     except:
#        return '-1'
#
# def get_config(group,config_name):
#     config = ConfigParser.ConfigParser()
#     config.readfp(open('./myapp/etc/config.ini','r'))
#     config_value=config.get(group,config_name).strip(' ').strip('\'').strip('\"')
#     return config_value
#
# def filters(data):
#     return data.strip(' ').strip('\n').strip('\br')
#
# host = get_config('settings','host')
# port = get_config('settings','port')
# user = get_config('settings','user')
# passwd = get_config('settings','passwd')
# dbname = get_config('settings','dbname')
# select_limit = int(get_config('settings','select_limit'))
# export_limit = int(get_config('settings','export_limit'))
# wrong_msg = get_config('settings','wrong_msg')
# public_user = get_config('settings','public_user')

# host = config.host
# port = config.port
# user = config.user
# passwd = config.passwd
# dbname = config.dbname

host = settings.DATABASES['default']['HOST']
port = settings.DATABASES['default']['PORT']
user = settings.DATABASES['default']['USER']
passwd = settings.DATABASES['default']['PASSWORD']
dbname = settings.DATABASES['default']['NAME']
select_limit = int(settings.SELECT_LIMIT)
export_limit = int(settings.EXPORT_LIMIT)
wrong_msg = settings.WRONG_MSG
public_user = settings.PUBLIC_USER
sqladvisor = settings.SQLADVISOR
advisor_switch = settings.SQLADVISOR_SWITCH
path_mysqldiff = settings.PATH_TO_MYSQLDIFF
#
# exceptlist = ["'","`","\""]
#
# def sql_init_filter(sqlfull):
#     tmp = oldp = sql = ''
#     sqllist = []
#     flag = 0
#     sqlfull = sqlfull.replace('\r','\n').strip()
#     try:
#         if sqlfull[-1]!=";":
#             sqlfull = sqlfull + ";"
#     except Exception,e:
#         pass
#     for i in sqlfull.split('\n'):
#         if len(i)>=2:
#             if i[0] == '-' and i[1] == '-' :
#                 continue
#         if len(i)>=1:
#             if i[0] == '#' :
#                 continue
#         if len(i)!=0:
#             tmp = tmp + i + '\n'
#
#     sqlfull = tmp
#     tmp = ''
#     i=0
#     while i<= (0 if len(sqlfull)==0 else len(sqlfull)-1):
#         if sqlfull[i] =='*' and oldp == '/'and flag == 0 :
#             flag = 2
#             sql = sql + sqlfull[i]
#         elif sqlfull[i] == '/' and oldp == '*' and flag == 2:
#             flag = 0
#             sql = sql + sqlfull[i]
#         elif sqlfull[i] == tmp and flag == 1:
#             flag = 0
#             sql = sql + sqlfull[i]
#             tmp=''
#         elif sqlfull[i] in exceptlist and flag == 0 and oldp != "\\":
#             tmp = sqlfull[i]
#             flag = 1
#             sql = sql + sqlfull[i]
#         elif sqlfull[i] == ';' and flag == 0:
#             sql = sql + sqlfull[i]
#             if len(sql) > 1:
#                 sqllist.append(sql)
#             sql = ''
#         # eliminate '#' among the line
#         elif sqlfull[i] == '#' and flag == 0:
#             flag =3
#         elif flag==3:
#             if sqlfull[i] == '\n':
#                 flag=0
#                 sql = sql + sqlfull[i]
#         else:
#             sql = sql + sqlfull[i]
#         oldp = sqlfull[i]
#         i=i+1
#     return sqllist
#
#
# def get_sql_detail(sqllist,flag):
#
#     query_type = ['desc','describe','show','select','explain']
#     dml_type = ['insert', 'update', 'delete', 'create', 'alter','rename', 'drop', 'truncate', 'replace']
#     if flag == 1:
#         list_type = query_type
#     elif flag ==2:
#         list_type = dml_type
#     typelist = []
#     i = 0
#     while i <= (0 if len(sqllist) == 0 else len(sqllist) - 1):
#         try:
#             type = sqllist[i].split()[0].lower()
#             if len(type)> 1:
#                 if type in list_type:
#                     #filter create or drop database,user
#                     if type == 'create' or type == 'drop' or type == 'alter':
#                         if sqllist[i].split()[1].lower() in ['database','user']:
#                             sqllist.pop(i)
#                             #i=i+1
#                             continue
#                     typelist.append(type)
#                     i = i + 1
#                 else:
#                     sqllist.pop(i)
#             else:
#                 sqllist.pop(i)
#         except:
#             i = i + 1
#
#     return sqllist


def mysql_query(sql,user=user,passwd=passwd,host=host,port=int(port),dbname=dbname,limitnum=select_limit):
    try:
        conn=MySQLdb.connect(host=host,user=user,passwd=passwd,port=int(port),db=None,connect_timeout=2,charset='utf8')
        if dbname:
            conn.select_db(dbname)
        cursor = conn.cursor()
        count=cursor.execute(sql)
        index=cursor.description
        col=[]
        #get column name
        for i in index:
            col.append(i[0])
        #result=cursor.fetchall()
        result=cursor.fetchmany(size=int(limitnum))
        cursor.close()
        conn.close()
        return (result,col)
    except Exception,e:
        return([str(e)],''),['error']
#获取下拉菜单列表

def get_hostlist(request,tag='tag'):
    permission_list = ''
    if tag == 'query':
        permission_list = ('read','read_write','all')
    elif tag == 'exec':
        permission_list = ('write', 'read_write', 'all')
    elif tag == 'log':
        permission_list = ('read', 'read_write', 'all')
    elif tag == 'meta':
        permission_list = ('read', 'read_write', 'all')
    elif tag == 'incep':
        permission_list = ('write', 'read_write', 'all')

    elif tag == 'admin':
        permission_list = ('admin')

    if request.GET.has_key('host_group'):
        selected_group = request.GET.get('host_group')
        login_user = request.user.username
        user_info =UserInfo.objects.get(username=login_user)
        host = Host.objects.filter(group=selected_group)
        ip_list = list(set([x.ip for x in host]))
        if tag == 'admin':
            db_instances = Db_instance.objects.filter(ip__in=tuple(ip_list),db_type='mysql',status='InUse',admin_user = user_info)

        else:
            db_instances = Db_instance.objects.filter(db_account__db_name__db_database_permission__account__id=user_info.id, ip__in=tuple(ip_list),
                                                  db_type='mysql',status='InUse',db_account__db_name__db_database_permission__permission__in=permission_list).distinct()
        db_list = []
        for instance in db_instances:
            id = instance.id
            ip = instance.ip
            port = instance.port
            explain = instance.comments
            db_list.append({'id':id, 'port':port, 'ip':ip, 'explain':explain})

        return db_list
    elif request.GET.has_key('instance_id'):
        instance_id = request.GET.get('instance_id')
        login_user = UserInfo.objects.get(username=request.user.username)

        dbs = Db_database_permission.objects.filter(account_id=login_user.id, permission__in=permission_list)\
                                                .filter(db_name__dbaccount__instance__id=int(instance_id))\
                                                .values('db_name__dbaccount__id','db_name__dbaccount__db_account_role','db_name__dbname','db_name__dbtag')
        data = []
        for db in dbs:
            db_account_id = db['db_name__dbaccount__id']
            db_account_role = db['db_name__dbaccount__db_account_role']
            db_name = db['db_name__dbname']
            db_tag = db['db_name__dbtag']
            data.append({'db_account_id':db_account_id,'db_account_role':db_account_role,'db_name':db_name,'db_tag':db_tag})


        return data


def get_mysql_hostlist(username,tag='tag',search=''):
    dbtype='mysql'
    host_list = []
    if len(search) == 0:
        if (tag=='tag'):
            a = UserInfo.objects.get(username=username)

            #如果没有对应role='read'或者role='all'的account账号，则不显示在下拉菜单中
            # for row in a.db_name_set.all().order_by("dbtag"):
            #     if row.db_account_set.all().filter(role__in=['read','all']):
            #         if row.instance.all().filter(role__in=['read','all']).filter(db_type=dbtype):
            #             host_list.append(row.dbtag)
            for row in a.db_name_set.filter(db_account__role__in=['read','all']).filter(
                    instance__role__in=['read','all']).filter(instance__db_type=dbtype).values(
                    'dbtag').distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag=='log'):
            for row in Db_name.objects.values('dbtag').distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag=='exec'):
            a = UserInfo.objects.get(username=username)
            #如果没有对应role='write'或者role='all'的account账号，则不显示在下拉菜单中
            # for row in a.db_name_set.all().order_by("dbtag"):
            #     if row.db_account_set.all().filter(role__in=['write','all']):
            # #排除只读实例
            #         if row.instance.all().filter(role__in=['write','all']).filter(db_type=dbtype):
            #             host_list.append(row.dbtag)

            for row in a.db_name_set.filter(db_account__role__in=['write', 'all']).filter(
                    instance__role__in=['write', 'all']).filter(instance__db_type=dbtype).values(
                    'dbtag').all().distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag == 'incept'):
            a = UserInfo.objects.get(username=username)
            # for row in a.db_name_set.all().order_by("dbtag"):
            #     #find the account which is admin
            #     if row.db_account_set.all().filter(role='admin'):
            #         if row.instance.all().filter(role__in=['write','all']).filter(db_type=dbtype):
            #         #if row.instance.all().exclude(role='read'):
            #             host_list.append(row.dbtag)
            for row in a.db_name_set.filter(db_account__role='admin').filter(
                    instance__role__in=['write', 'all']).filter(instance__db_type=dbtype).values(
                    'dbtag').all().distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag == 'meta'):
            # for row in Db_name.objects.all().order_by("dbtag"):
            #     #find the account which is admin
            #     if row.db_account_set.all().filter(role='admin'):
            #         if row.instance.filter(role__in=['write','all','read']).filter(db_type=dbtype):
            #             host_list.append(row.dbtag)
            for row in Db_name.objects.filter(db_account__role='admin').filter(
                    instance__role__in=['write', 'all','read']).filter(instance__db_type=dbtype).values(
                    'dbtag').all().distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
    elif len(search) > 0:
        if (tag=='tag'):
            a = UserInfo.objects.get(username=username)
            #如果没有对应role='read'或者role='all'的account账号，则不显示在下拉菜单中
            # for row in a.db_name_set.filter(dbname__contains=search).order_by("dbtag"):
            #     if row.db_account_set.all().filter(role__in=['read','all']):
            #         if row.instance.all().filter(role__in=['read','all']).filter(db_type=dbtype):
            #             host_list.append(row.dbtag)
            for row in a.db_name_set.filter(dbname__contains=search).filter(db_account__role__in=['read', 'all']).filter(
                    instance__role__in=['read', 'all']).filter(instance__db_type=dbtype).values(
                    'dbtag').distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag=='log'):
            for row in Db_name.objects.values('dbtag').distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag=='exec'):
            a = UserInfo.objects.get(username=username)
            #如果没有对应role='write'或者role='all'的account账号，则不显示在下拉菜单中
            # for row in a.db_name_set.filter(dbname__contains=search).order_by("dbtag"):
            #     if row.db_account_set.all().filter(role__in=['write','all']):
            # #排除只读实例
            #         if row.instance.all().filter(role__in=['write','all']).filter(db_type=dbtype):
            #             host_list.append(row.dbtag)
            for row in a.db_name_set.filter(dbname__contains=search).filter(db_account__role__in=['write', 'all']).filter(
                    instance__role__in=['write', 'all']).filter(instance__db_type=dbtype).values(
                    'dbtag').all().distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag == 'incept'):
            a = UserInfo.objects.get(username=username)
            # for row in a.db_name_set.filter(dbname__contains=search).order_by("dbtag"):
            #     #find the account which is admin
            #     if row.db_account_set.all().filter(role='admin'):
            #         if row.instance.all().filter(role__in=['write','all']).filter(db_type=dbtype):
            #         #if row.instance.all().exclude(role='read'):
            #             host_list.append(row.dbtag)
            for row in a.db_name_set.filter(dbname__contains=search).filter(db_account__role='admin').filter(
                    instance__role__in=['write', 'all']).filter(instance__db_type=dbtype).values(
                    'dbtag').all().distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
        elif (tag == 'meta'):
            # for row in Db_name.filter(dbname__contains=search).order_by("dbtag"):
            #     #find the account which is admin
            #     if row.db_account_set.all().filter(role='admin'):
            #         if row.instance.filter(role__in=['write','all','read']).filter(db_type=dbtype):
            #             host_list.append(row.dbtag)
            for row in Db_name.objects.filter(dbname__contains=search).filter(db_account__role='admin').filter(
                    instance__role__in=['write', 'all','read']).filter(instance__db_type=dbtype).values(
                    'dbtag').all().distinct().order_by("dbtag"):
                host_list.append(row['dbtag'])
    return host_list





def get_op_type(methods='get'):
    #all表示所有种类
    op_list=['all','incept','truncate','drop','create','delete','update','replace','insert','select','explain','alter','rename','show']
    if (methods=='get'):
        return op_list


def get_connection_info(hosttag,request):
    # 确认dbname
    a = Db_name.objects.filter(dbtag=hosttag)[0]
    # a = Db_name.objects.get(dbtag=hosttag)
    tar_dbname = a.dbname
    # 如果instance中有备库role='read'，则选择从备库读取
    try:
        if a.instance.all().filter(role='read')[0]:
            tar_host = a.instance.all().filter(role='read')[0].ip
            tar_port = a.instance.all().filter(role='read')[0].port
    # 如果没有设置或没有role=read，则选择第一个读到的all实例读取
    except Exception, e:
        tar_host = a.instance.filter(role='all')[0].ip
        tar_port = a.instance.filter(role='all')[0].port
        # tar_host = a.instance.all()[0].ip
        # tar_port = a.instance.all()[0].port
    pc = prpcrypt()
    for i in a.db_account_set.all():
        if i.role != 'write' and i.role != 'admin':
            # find the specified account for the user
            if i.account.all().filter(username=request.user.username):
                tar_username = i.user
                tar_passwd = pc.decrypt(i.passwd)
                break
    # not find specified account for the user ,specified the public account to the user

    if not vars().has_key('tar_username'):
        for i in a.db_account_set.all():
            if i.role != 'write' and i.role != 'admin':
                # find the specified account for the user
                if i.account.all().filter(username=public_user):
                    tar_username = i.user
                    tar_passwd = pc.decrypt(i.passwd)
                    break
    return tar_port,tar_passwd,tar_username,tar_host,tar_dbname


def get_advice(hosttag, sql, request):
    if advisor_switch!=0:
        tar_port, tar_passwd, tar_username, tar_host,tar_dbname = get_connection_info(hosttag,request)
        # print tar_port+tar_passwd+tar_username+tar_host
        sql=sql.replace('"','\\"').replace('`', '\`')[:-1]
        cmd = sqladvisor+ ' -u %s -p %s -P %d -h %s -d %s -v 1 -q "%s"' %(tar_username,tar_passwd,int(tar_port),tar_host,tar_dbname,sql)
        # print cmd
        status,result_tmp = commands.getstatusoutput(cmd)
        # print result_tmp
        result_list = result_tmp.split('\n')
        results=''
        for i in result_list:
            try:
                unicode(i, 'utf-8')
                results=results+'\n'+i
            except Exception,e:
                pass

        # results = results.replace('\xc0',' ').replace('\xbf',' ')
        print results
    else:
        results = 'sqladvisor not configured yet.'
    return results


def get_mysql_data(db_account,sql,useraccount,request,limitnum):
    #确认dbname
    # a = Db_name.objects.filter(dbtag=hosttag)[0]
    # #a = Db_name.objects.get(dbtag=hosttag)
    # tar_dbname = a.dbname
    # #如果instance中有备库role='read'，则选择从备库读取
    # try:
    #     if a.instance.all().filter(role='read')[0]:
    #         tar_host = a.instance.all().filter(role='read')[0].ip
    #         tar_port = a.instance.all().filter(role='read')[0].port
    # #如果没有设置或没有role=read，则选择第一个读到的all实例读取
    # except Exception,e:
    #     tar_host = a.instance.filter(role='all')[0].ip
    #     tar_port = a.instance.filter(role='all')[0].port
    #     # tar_host = a.instance.all()[0].ip
    #     # tar_port = a.instance.all()[0].port
    # pc = prpcrypt()
    # for i in a.db_account_set.all():
    #     if i.role!='write' and i.role!='admin':
    #         # find the specified account for the user
    #         if i.account.all().filter(username=useraccount):
    #             tar_username = i.user
    #             tar_passwd = pc.decrypt(i.passwd)
    #             break
    # #not find specified account for the user ,specified the public account to the user
    # if not vars().has_key('tar_username'):
    #     for i in a.db_account_set.all():
    #         if i.role != 'write' and i.role != 'admin':
    #             # find the specified account for the user
    #             if i.account.all().filter(username=public_user):
    #                 tar_username = i.user
    #                 tar_passwd = pc.decrypt(i.passwd)
    #                 break

    #print tar_port+tar_passwd+tar_username+tar_host
    pc = prpcrypt()
    tar_username = db_account.user
    tar_passwd = pc.decrypt(db_account.passwd)
    tar_host = db_account.instance.ip
    tar_port = db_account.instance.port
    tar_dbname = request.POST['optionsRadios'].split(':')[1]
    db_tag = db_account.instance.ip+':'+db_account.instance.port+'__'+db_account.db_account_role
    try:
        if (cmp(sql,wrong_msg)):
            log_mysql_op(useraccount,sql,tar_dbname,db_tag,request)
        results,col = mysql_query(sql,tar_username,tar_passwd,tar_host,tar_port,tar_dbname,limitnum)
    except Exception, e:
        #防止日志库记录失败，返回一个wrong_message
        results,col = ([str(e)],''),['error']
        #results,col = mysql_query(wrong_msg,user,passwd,host,int(port),dbname)
    return results,col,tar_dbname


#检查输入语句,并返回行限制数
def check_mysql_query(sqltext,user,type='select'):
    #根据user确定能够select或者export 的行数
    if (type=='export'):
        try :
            num = UserInfo.objects.get(username=user).user_profile.export_limit
        except Exception, e:
            num = export_limit
    elif (type=='select'):
        try :
            num = UserInfo.objects.get(username=user).user_profile.select_limit
        except Exception, e:
            num = select_limit
    num=str(num)
    limit = ' limit '+ num

    sqltext = sqltext.strip()
    sqltype = sqltext.split()[0].lower()
    list_type = ['select','show','desc','explain','describe']
    #flag 1位有效 0为list_type中的无效值
    flag=0
    while True:
        sqltext = sqltext.strip()
        lastletter = sqltext[len(sqltext)-1]
        if (not cmp(lastletter,';')):
            sqltext = sqltext[:-1]
        else:
            break
    #判断语句中是否已经存在limit，has_limit 为0时说明原来语句中是有limit的
    try:
        has_limit = cmp(sqltext.split()[-2].lower(),'limit')
    except Exception,e:
        #prevent some input like '1' or 'ss' ...
        return wrong_msg, num

    for i in list_type:
        if (not cmp(i,sqltype)):
            flag=1
            break
    if (flag==1):
        if (sqltype =='select' and has_limit!=0):
            return sqltext+limit,num
        elif (sqltype =='select' and has_limit==0):
            if (int(sqltext.split()[-1])<= int(num) ):
                return sqltext,num
            else:
                tempsql=''
                numlimit=sqltext.split()[-1]
                for i in sqltext.split()[0:-1]:
                    tempsql=tempsql+i+' '
                return tempsql+num,num
        else:
            return sqltext,num
    else:
        return wrong_msg,num

#记录用户所有操作
def log_mysql_op(user,sqltext,mydbname,dbtag,request):
    user = UserInfo.objects.get(username=user)
    #lastlogin = user.last_login+datetime.timedelta(hours=8)
    #create_time = timezone.now()+datetime.timedelta(hours=8)
    lastlogin = user.last_login
    create_time = timezone.now()
    username = user.username
    sqltype=sqltext.split()[0].lower()
    instance = Db_instance.objects.get(ip=dbtag.split(':')[0],port=dbtag.split(':')[1].split('__')[0])
    group_id = Host.objects.get(ip=instance.ip).group_id
    if sqltype in ['desc','describe']:
        sqltype='show'
    #获取ip地址
    ipaddr = get_client_ip(request)
    log = Oper_log (host_id=instance.id, group_id=group_id, user=username,sqltext=sqltext,sqltype=sqltype,login_time=lastlogin,create_time=create_time,dbname=mydbname,dbtag=dbtag,ipaddr=ipaddr)
    log.save()
    return 1

def log_mongo_op(sqltext,dbtag,tbname,request):
    user = UserInfo.objects.get(username=request.user.username)
    lastlogin = user.last_login
    create_time = timezone.now()
    username = user.username
    sqltype='select'
    ipaddr = get_client_ip(request)
    log = Oper_log (user=username,sqltext=sqltext,sqltype=sqltype,login_time=lastlogin,create_time=create_time,dbname=tbname,dbtag=dbtag,ipaddr=ipaddr)
    log.save()
    return 1

def log_userlogin(request):
    username = request.user.username
    user = UserInfo.objects.get(username=username)
    ipaddr = get_client_ip(request)
    action = 'login'
    create_time = timezone.now()
    log = Login_log(user=username,ipaddr=ipaddr,action=action,create_time=create_time)
    log.save()

def log_loginfailed(request,username):

    ipaddr = get_client_ip(request)
    action = 'login_failed'
    create_time = timezone.now()
    log = Login_log(user=username, ipaddr=ipaddr, action=action,create_time=create_time)
    log.save()

def get_log_data(select_group,select_host,optype,begin,end):
    if select_group == 0:
        if (optype=='all'):
            #如果结束时间小于开始时间，则以结束时间为准

            if (end > begin):
                log = Oper_log.objects.filter(create_time__lte=end).filter(create_time__gte=begin).order_by("-create_time")[0:100]
            else:
                log = Oper_log.objects.filter(create_time__lte=end).order_by("-create_time")[0:100]
        else:
            if (end > begin):
                log = Oper_log.objects.filter(sqltype=optype).filter(create_time__lte=end).filter(create_time__gte=begin).order_by("-create_time")[0:100]
            else:
                log = Oper_log.objects.filter(sqltype=optype).filter(create_time__lte=end).order_by("-create_time")[0:100]
        return log
    elif select_host ==0 :
        if (optype == 'all'):
            # 如果结束时间小于开始时间，则以结束时间为准

            if (end > begin):
                log = Oper_log.objects.filter(group_id=select_group).filter(create_time__lte=end).filter(create_time__gte=begin).order_by(
                    "-create_time")[0:100]
            else:
                log = Oper_log.objects.filter(group_id=select_group).filter(create_time__lte=end).order_by("-create_time")[0:100]
        else:
            if (end > begin):
                log = Oper_log.objects.filter(group_id=select_group).filter(sqltype=optype).filter(create_time__lte=end).filter(
                    create_time__gte=begin).order_by("-create_time")[0:100]
            else:
                log = Oper_log.objects.filter(group_id=select_group).filter(sqltype=optype).filter(
                    create_time__lte=end).order_by("-create_time")[0:100]
        return log
    else:
        if (optype == 'all'):
            # 如果结束时间小于开始时间，则以结束时间为准

            if (end > begin):
                log = Oper_log.objects.filter(group_id=select_group, host_id=select_host).filter(create_time__lte=end).filter(
                    create_time__gte=begin).order_by(
                    "-create_time")[0:100]
            else:
                log = Oper_log.objects.filter(group_id=select_group, host_id=select_host).filter(create_time__lte=end).order_by(
                    "-create_time")[0:100]
        else:
            if (end > begin):
                log = Oper_log.objects.filter(group_id=select_group, host_id=select_host).filter(sqltype=optype).filter(
                    create_time__lte=end).filter(
                    create_time__gte=begin).order_by("-create_time")[0:100]
            else:
                log = Oper_log.objects.filter(group_id=select_group, host_id=select_host).filter(sqltype=optype).filter(create_time__lte=end).order_by("-create_time")[0:100]
        return log


def check_explain (sqltext):
    sqltext = sqltext.strip()
    sqltype = sqltext.split()[0].lower()
    if (sqltype =='select'):
        sqltext = 'explain extended '+sqltext
        return sqltext
    else:
        return wrong_msg
#
# def my_key(group, request):
#     try:
#         real_ip = request.META['HTTP_X_FORWARDED_FOR']
#         regip = real_ip.split(",")[0]
#     except:
#         try:
#             regip = request.META['REMOTE_ADDR']
#         except:
#             regip = ""
#     form = LoginForm(request.POST)
#     myform = Captcha(request.POST)
#     #验证码正确情况下，错误密码登录次数
#     if form.is_valid() and myform.is_valid():
#         username = form.cleaned_data['username']
#         # password = form.cleaned_data['password']
#
#         return regip+username
#     #验证码错误不计算
#     else:
#         return regip+str(uuid.uuid1())


def get_client_ip(request):
    try:
        real_ip = request.META['HTTP_X_FORWARDED_FOR']
        regip = real_ip.split(",")[0]
    except:
        try:
            regip = request.META['REMOTE_ADDR']
        except:
            regip = ""
    return regip

def check_mysql_exec(sqltext,request,type='dml'):
    try:
        sqltext = sqltext.strip()
        sqltype = sqltext.split()[0].lower()
        db_account_id, db_name = request.POST.get('optionsRadios').split(':')
        a = Db_database_permission_detail.objects.filter(permission__db_name__dbname=db_name,
                                                         permission__db_name__dbaccount__id=db_account_id)
        if len(a) ==0:
            return "select 'Don\\'t have any permission,please concat dba'"
        else:
            if sqltype in json.loads(a[0].permission_detail):
                return sqltext
            else:
                return "select 'Don\\'t have permission to \"{}\"'".format(sqltype)
    except Exception,e:
        print(e)

        return wrong_msg

def run_mysql_exec(db_account,sql,useraccount,request):
    pc = prpcrypt()
    tar_username = db_account.user
    tar_passwd = pc.decrypt(db_account.passwd)
    tar_host = db_account.instance.ip
    tar_port = db_account.instance.port
    tar_dbname = request.POST['optionsRadios'].split(':')[1]
    db_tag = db_account.instance.ip + ':' + db_account.instance.port + '__' + db_account.db_account_role

    try:
        if (sql.split()[0] != 'select'):
            log_mysql_op(useraccount, sql, tar_dbname, db_tag, request)
            results, col = mysql_exec(sql, tar_username, tar_passwd, tar_host, tar_port, tar_dbname)
        else:
            results, col = mysql_query(sql, user, passwd, host, int(port), dbname)
    except Exception, e:
        results, col = ([str(e)], ''), ['error']
        #防止日志库记录失败，返回一个wrong_message
        #results,col = mysql_query(wrong_msg,user,passwd,host,int(port),dbname)
    return results,col,tar_dbname



def mysql_exec(sql,user=user,passwd=passwd,host=host,port=int(port),dbname=dbname):
    try:
        conn=MySQLdb.connect(host=host,user=user,passwd=passwd,port=int(port),connect_timeout=5,charset='utf8')
        conn.select_db(dbname)
        curs = conn.cursor()
        result=curs.execute(sql)
        conn.commit()
        curs.close()
        conn.close()
        return (['影响行数: '+str(result)],''),['success']
    except Exception,e:
        if str(e)=='(2014, "Commands out of sync; you can\'t run this command now")':
            return (['只能输入单条sql语句'],''),['error']
        else:
            return([str(e)],''),['error']


def get_pre(dbtag):
    db = Db_name.objects.get(dbtag=dbtag)
    ins = db.instance.all()
    acc = db.account.all()
    acc_list = Db_account.objects.filter(dbname=db)
    gp = db.db_group_set.all()
    return acc_list,ins,acc,gp

def get_user_pre(username,request):
    if len(username)<=30:
        try :
            info = "PRIVILEGES FOR " + username
            dblist = UserInfo.objects.get(username=username).db_name_set.all()
        except :
            info = "PLEASE CHECK YOUR INPUT"
            dblist = UserInfo.objects.get(username=request.user.username).db_name_set.all()
    else:
        info = "INPUT TOO LONG"
        dblist = UserInfo.objects.get(username=request.user.username).db_name_set.all()
    return dblist,info

#used in prequery.html
def get_groupdb(group):
    grouplist = Db_group.objects.filter(groupname=group)
    return grouplist

#used in prequery.html
def get_privileges(username):
    pri = UserInfo.objects.get(username=username).user_permissions.all()
    return pri

def get_UserAndGroup():
    user_list = UserInfo.objects.exclude(username=public_user).order_by('username')
    group_list = Db_group.objects.all().order_by('groupname')

    # for row in UserInfo.objects.all():
    #     user_list.append(row.username)
    return user_list,group_list

def get_user_grouppri(username):
    user = UserInfo.objects.get(username=username)
    a = user.db_group_set.all()
    b = user.groups.all()
    return  a,b

def clear_userpri(username):
    user = UserInfo.objects.get(username=username)
    for i in Db_name.objects.all():
        i.account.remove(user)
    for i in Db_group.objects.all():
        i.account.remove(user)
    user.user_permissions.clear()
    user.groups.clear()

def set_groupdb(username,li):
    user = UserInfo.objects.get(username=username)
    tag_list=[]
    for i in li:
        tmp_gp = Db_group.objects.get(id=i)
        try:
            tmp_gp.account.add(user)
        except Exception,e:
            pass

        for x in tmp_gp.dbname.all():
            tag_list.append(x.dbtag)
            try:
                x.account.add(user)
            except Exception,e:
                pass
    tag_list = list(set(tag_list))
    return tag_list

#create user in pre_set.html
def create_user(username,passwd,mail):
    if len(username)>0 and len(passwd)>0 and len(mail)>0:
        user = UserInfo.objects.create_user(username=username,password=passwd,email=mail)
        user.save()
    return user
#delete user in pre_set.html
def delete_user(username):
    user = UserInfo.objects.get(username=username)
    user.delete()

#user dbtaglist and user to set user-db relation
def set_user_db(user,dblist):
    setdblist = Db_name.objects.filter(dbtag__in=dblist)
    for i in setdblist:
        try:
            i.account.add(user)
            i.save()
        except Exception,e:
            pass

# a = Permission.objects.filter(codename__istartswith='can')


def set_usergroup(user,group):
    # user.groups.clear()
    grouplist = Group.objects.filter(name__in=group)
    for i in grouplist:
        try:
            user.groups.add(i)
            user.save()
        except Exception,e:
            pass
    # for i in a:
    #     print i.codename

def get_usergp_list():
    # perlist = Permission.objects.filter(codename__istartswith='can')
    grouplist = Group.objects.all().order_by('name')
    return grouplist

def get_diff(dbtag1,tb1,dbtag2,tb2):

    if os.path.isfile(path_mysqldiff) :
        tar_host1, tar_port1, tar_username1, tar_passwd1,tar_dbname1 = get_conn_info(dbtag1)
        tar_host2, tar_port2, tar_username2, tar_passwd2,tar_dbname2 = get_conn_info(dbtag2)

        server1 = ' -q --server1={}:{}@{}:{}'.format(tar_username1,tar_passwd1,tar_host1,str(tar_port1))
        server2 = ' --server2={}:{}@{}:{}'.format(tar_username2,tar_passwd2,tar_host2,str(tar_port2))
        option = ' --difftype=sql'
        table = ' {}.{}:{}.{}'.format(tar_dbname1,tb1,tar_dbname2,tb2)
        cmd = path_mysqldiff + server1 + server2 + option + table
        output = os.popen(cmd)
        result = output.read()
        # result = commands.getoutput(cmd)
    else :
        result = "mysqldiff not installed"

    return result

def get_conn_info(hosttag):
    a = Db_name.objects.filter(dbtag=hosttag)[0]
    #a = Db_name.objects.get(dbtag=hosttag)
    tar_dbname = a.dbname
    #如果instance中有备库role='read'，则选择从备库读取
    try:
        if a.instance.all().filter(role='read')[0]:
            tar_host = a.instance.all().filter(role='read')[0].ip
            tar_port = a.instance.all().filter(role='read')[0].port
    #如果没有设置或没有role=read，则选择第一个读到的实例读取
    except Exception,e:
        tar_host = a.instance.filter(role__in=['write','all'])[0].ip
        tar_port = a.instance.filter(role__in=['write','all'])[0].port
    pc = prpcrypt()
    for i in a.db_account_set.all():
        if i.role == 'admin':
            tar_username = i.user
            tar_passwd = pc.decrypt(i.passwd)
            break
    return tar_host,tar_port,tar_username,tar_passwd,tar_dbname




def generate_token(key, expire=3600):

    ts_str = str(time.time() + expire)
    ts_byte = ts_str.encode("utf-8")
    print(type(ts_byte))
    sha1_tshexstr  = hmac.new(key.encode("utf-8"),ts_byte).hexdigest()
    token = ts_str+':'+sha1_tshexstr
    b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
    return b64_token.decode("utf-8")

def format_data(data,flag):
    if flag == 'title':
        return [{'title':t} for t in data]


def main():
    return 1
if __name__=='__main__':

    main()
