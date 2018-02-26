#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render, HttpResponse
import ConfigParser
from dbmanage.bkrs.models import *
from cmdb.models import HostGroup,Host
import os
from django.middleware import csrf
from django.contrib.auth.decorators import login_required
from accounts.permission import permission_verify
from django.contrib.auth import get_user_model
from lib.log import dic
import py_compile
import json

import datetime
from lib.common import token_verify
from django.views.decorators.csrf import csrf_exempt

from dbmanage.myapp.include.encrypt import prpcrypt

@login_required()
@permission_verify()
def index1(request):
    '''
    [04/Nov/2017 21:22:01] "GET /dbmanage/?
    csrfmiddlewaretoken=AGmegYcTyfSVvXHZ5TpXLM44ToAuvCphfHyXgx91cCfXWF8gEnimyt8wRzCtkRbV
    &group=1
    &host=0 
    HTTP/1.1" 200 11575
    :param request: 
    :return: 
    '''
    temp_name = 'dbmanage/dbmanage_header.html'
    select_group_id=request.GET.get('group')
    select_host_id = request.GET.get('host')
    group = HostGroup.objects.all()
    group_list = []
    host_list = []
    for g in group:
        group_list.append({'group_id': g.id, 'group_name': g.name})
    if select_group_id is None:
        select_group_id = 0
    if int(select_group_id) > 0:
        selected_group_name = HostGroup.objects.values('name').filter(id=select_group_id)[0]['name']

        h = Host.objects.values('id','hostname','ip').filter(group=int(select_group_id)).order_by('hostname')
        for hi in h:
            host_list.append({'host_id':hi['id'],'hostname':hi['hostname'],'host_ip':hi['ip']})

    return render(request,'dbmanage/index.html',locals())

@login_required()
@permission_verify()
def edit_conf(request):
    if request.GET.get('host') > 0:
        host_id = request.GET.get('host')

        if host_id:
            hostname,host_ip = Host.objects.values_list('hostname','ip').get(id=host_id)

            temp_name = "dbmanage/dbmanage_header.html"
            display_control = "True"
            dirs = os.path.dirname(os.path.abspath(__file__))
            config = ConfigParser.ConfigParser()
            all_level = dic
            configfile = dirs+'/conf/base.conf'
            f = dirs+'/conf/{hostname}_{ip}.conf'.format(hostname=hostname,ip='_'.join(host_ip.split('.')))
            configfile_exists = 0
            if os.path.isfile(f):
                configfile = f
                configfile_exists =1

            select_group_id = request.GET.get('group')
            select_host_id = request.GET.get('host')
            group = HostGroup.objects.all()
            group_list = []
            host_list = []
            for g in group:
                group_list.append({'group_id': g.id, 'group_name': g.name})
            if select_group_id is None:
                select_group_id = 0
            if int(select_group_id) > 0:
                selected_group_name = HostGroup.objects.values('name').filter(id=select_group_id)[0]['name']

                h = Host.objects.values('id', 'hostname', 'ip').filter(group=int(select_group_id)).order_by('hostname')
                for hi in h:
                    host_list.append({'host_id': hi['id'], 'hostname': hi['hostname'], 'host_ip': hi['ip']})

                if int(select_host_id) > 0:
                    for l in host_list:
                        if l['host_id'] == int(select_host_id):
                            selected_hostname = l['hostname']


            with open(configfile, 'r') as cfgfile:
                config.readfp(cfgfile)

                xbs_decrypt = config.get('Xbstream', 'xbs_decrypt')
                xbstream = config.get('Xbstream', 'xbstream')
                remote_stream = config.get('Xbstream', 'remote_stream')
                xbstream_options = config.get('Xbstream', 'xbstream_options')
                stream = config.get('Xbstream', 'stream')
                remote_dir = config.get('Remote', 'remote_dir')
                remote_conn = config.get('Remote', 'remote_conn')
                remove_original = config.get('Compress', 'remove_original')
                compress = config.get('Compress', 'compress')
                compress_chunk_size = config.get('Compress', 'compress_chunk_size')
                compress_threads = config.get('Compress', 'compress_threads')
                decompress = config.get('Compress', 'decompress')
                chown_command = config.get('Commands', 'chown_command')
                start_mysql_command = config.get('Commands', 'start_mysql_command')
                stop_mysql_command = config.get('Commands', 'stop_mysql_command')
                mysql_password = config.get('MySQL', 'mysql_password')
                mysql_host = config.get('MySQL', 'mysql_host')
                datadir = config.get('MySQL', 'datadir')
                mycnf = config.get('MySQL', 'mycnf')
                mysql_socket = config.get('MySQL', 'mysql_socket')
                mysqladmin = config.get('MySQL', 'mysqladmin')
                mysql_user = config.get('MySQL', 'mysql_user')
                mysql_port = config.get('MySQL', 'mysql_port')
                mysql = config.get('MySQL', 'mysql')
                encrypt = config.get('Encrypt', 'encrypt')
                xbcrypt = config.get('Encrypt', 'xbcrypt')
                encrypt_key = config.get('Encrypt', 'encrypt_key')
                remove_original = config.get('Encrypt', 'remove_original')
                decrypt = config.get('Encrypt', 'decrypt')
                encrypt_chunk_size = config.get('Encrypt', 'encrypt_chunk_size')
                encrypt_threads = config.get('Encrypt', 'encrypt_threads')
                encrypt_key_file = config.get('Encrypt', 'encrypt_key_file')
                xtra_prepare_options = config.get('Backup', 'xtra_prepare_options')
                backup_tool = config.get('Backup', 'backup_tool')
                archive_dir = config.get('Backup', 'archive_dir')
                prepare_tool = config.get('Backup', 'prepare_tool')
                pid_dir = config.get('Backup', 'pid_dir')
                full_backup_interval = config.get('Backup', 'full_backup_interval')
                max_archive_size = config.get('Backup', 'max_archive_size')
                xtra_prepare = config.get('Backup', 'xtra_prepare')
                xtra_options = config.get('Backup', 'xtra_options')
                tmpdir = config.get('Backup', 'tmpdir')
                partial_list = config.get('Backup', 'partial_list')
                xtra_backup = config.get('Backup', 'xtra_backup')
                max_archive_duration = config.get('Backup', 'max_archive_duration')
                pid_runtime_warning = config.get('Backup', 'pid_runtime_warning')
                optional = config.get('Backup', 'optional')
                backupdir = config.get('Backup', 'backupdir')
                gitcmd = config.get('TestConf', 'gitcmd')
                mysql_options = config.get('TestConf', 'mysql_options')
                ps_branches = config.get('TestConf', 'ps_branches')
                xb_configs = config.get('TestConf', 'xb_configs')
                testpath = config.get('TestConf', 'testpath')
                incremental_count = config.get('TestConf', 'incremental_count')

            cfgfile.close()
            # return HttpResponse('success')
            return render(request, 'dbmanage/edit.html',locals())
    else:
        return render(request,'dbmanage/index.html',locals())


@login_required()
@permission_verify()
def config_save(request):
    temp_name = "config/config-header.html"
    if request.method == 'POST':
        # path info
        ansible_path = request.POST.get('ansible_path')
        roles_path = request.POST.get('roles_path')
        pbook_path = request.POST.get('pbook_path')
        scripts_path = request.POST.get('scripts_path')
        # db info
        engine = request.POST.get('engine')
        host = request.POST.get('host')
        port = request.POST.get('port')
        user = request.POST.get('user')
        password = request.POST.get('password')
        database = request.POST.get('database')
        # cmdb_api_token
        token = request.POST.get('token')
        ssh_pwd = request.POST.get('ssh_pwd')
        # log info
        log_path = request.POST.get('log_path')
        log_level = request.POST.get('log_level')
        # mongodb info
        mongodb_ip = request.POST.get('mongodb_ip')
        mongodb_port = request.POST.get('mongodb_port')
        mongodb_user = request.POST.get('mongodb_user')
        mongodb_pwd = request.POST.get('mongodb_pwd')
        mongodb_collection = request.POST.get('mongodb_collection')
        # webssh domain
        webssh_domain = request.POST.get('webssh_domain')

        config = ConfigParser.RawConfigParser()
        dirs = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config.add_section('config')
        config.set('config', 'ansible_path', ansible_path)
        config.set('config', 'roles_path', roles_path)
        config.set('config', 'playbook_path', pbook_path)
        config.set('config', 'scripts_path', scripts_path)
        config.add_section('db')
        config.set('db', 'engine', engine)
        config.set('db', 'host', host)
        config.set('db', 'port', port)
        config.set('db', 'user', user)
        config.set('db', 'password', password)
        config.set('db', 'database', database)
        config.add_section('token')
        config.set('token', 'token', token)
        config.set('token', 'ssh_pwd', token)
        config.add_section('log')
        config.set('log', 'log_path', log_path)
        config.set('log', 'log_level', log_level)
        config.add_section('mongodb')
        config.set('mongodb', 'mongodb_ip', mongodb_ip)
        config.set('mongodb', 'mongodb_port', mongodb_port)
        config.set('mongodb', 'mongodb_user', mongodb_user)
        config.set('mongodb', 'mongodb_pwd', mongodb_pwd)
        config.set('mongodb', 'collection', mongodb_collection)
        config.add_section('webssh')
        config.set('webssh', 'domain', webssh_domain)
        tips = u"保存成功！"
        display_control = ""
        with open(dirs+'/adminset.conf', 'wb') as cfgfile:
            config.write(cfgfile)
        with open(dirs+'/adminset.conf', 'r') as cfgfile:
            config.readfp(cfgfile)
            a_path = config.get('config', 'ansible_path')
            r_path = config.get('config', 'roles_path')
            p_path = config.get('config', 'playbook_path')
            s_path = config.get('config', 'scripts_path')
            engine = config.get('db', 'engine')
            host = config.get('db', 'host')
            port = config.get('db', 'port')
            user = config.get('db', 'user')
            password = config.get('db', 'password')
            database = config.get('db', 'database')
            token = config.get('token', 'token')
            ssh_pwd = config.get('token', 'ssh_pwd')
            log_path = config.get('log', 'log_path')
            mongodb_ip = config.get('mongodb', 'mongodb_ip')
            mongodb_port = config.get('mongodb', 'mongodb_port')
            mongodb_user = config.get('mongodb', 'mongodb_user')
            mongodb_pwd = config.get('mongodb', 'mongodb_pwd')
            mongodb_collection = config.get('mongodb', 'collection')
            webssh_domain = config.get('webssh', 'domain')
    else:
        display_control = "none"
    return render(request, 'config/index.html', locals())


def get_dir(args):
    config = ConfigParser.RawConfigParser()
    dirs = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(dirs+'/adminset.conf', 'r') as cfgfile:
        config.readfp(cfgfile)
        a_path = config.get('config', 'ansible_path')
        r_path = config.get('config', 'roles_path')
        p_path = config.get('config', 'playbook_path')
        s_path = config.get('config', 'scripts_path')
        token = config.get('token', 'token')
        ssh_pwd = config.get('token', 'ssh_pwd')
        log_path = config.get('log', 'log_path')
        log_level = config.get('log', 'log_level')
        mongodb_ip = config.get('mongodb', 'mongodb_ip')
        mongodb_port = config.get('mongodb', 'mongodb_port')
        mongodb_user = config.get('mongodb', 'mongodb_user')
        mongodb_pwd = config.get('mongodb', 'mongodb_pwd')
        mongodb_collection = config.get('mongodb', 'collection')
        webssh_domain = config.get('webssh', 'domain')
    # 根据传入参数返回变量以获取配置，返回变量名与参数名相同
    if args:
        return vars()[args]
    else:
        return HttpResponse(status=403)



@login_required
def index(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    yesterday = str(datetime.date.today()-datetime.timedelta(days=1))
    day_count = count_day_status.objects.filter(count_date=yesterday).first()
    if day_count:
        back_success_file =day_count.back_file_success
        back_customers_success =day_count.back_customers_success
        back_file_failed =day_count.back_file_failed
        back_customers_failed =day_count.back_customers_failed
    else:
        back_success_file =0
        back_customers_success =0
        back_file_failed =0
        back_customers_failed =0

    mon_count = count_mon_status.objects.all().order_by('-id')[:12]
    customer_count = []
    customer_count_customer = []
    customer_count_file = []
    for mon_item in mon_count:
        mon_dict = {'y':str(mon_item.count_date),'a':str(mon_item.back_customers),'b':str(mon_item.back_customers_stop)}
        mon_dict_customer = {'period':str(mon_item.count_date),'platform':str(mon_item.back_customers)}
        mon_dict_file = {'period':str(mon_item.count_date),'file':str(mon_item.back_file)}
        customer_count.append(mon_dict)
        customer_count_customer.append(mon_dict_customer)
        customer_count_file.append(mon_dict_file)
    customer_count = customer_count[::-1]
    customer_count_customer = customer_count_customer[::-1]
    customer_count_file = customer_count_file[::-1]

    yes_backfailed = backfailed.objects.filter(count_date=yesterday).order_by('back_failed')[:12]
    # for i in range(0,int(4-len(yes_backfailed))):
    #     yes_backfailed.append(0)

    data = {'back_success_file':back_success_file,'back_customers_success':back_customers_success,
                               'back_file_failed':back_file_failed,'back_customers_failed':back_customers_failed,
                               'customer_count':str(customer_count),'customer_count_customer':str(customer_count_customer),
                               'customer_count_file':str(customer_count_file),'yes_backfailed':yes_backfailed}

    index_flag = True
    return render(request,'bkrs/base.html',locals())


@login_required()
def edit_backnode(request,id):
    backnode_id = int(id)
    if request.method == 'GET':
        backnode = BackupServer.objects.get(id=backnode_id)
        return render(request, 'bkrs/backnode_edit.html', locals())
    elif request.method == 'POST':
        try:
            name = request.POST['name']
            ip = request.POST['ip']
            port= request.POST['port']
            user = request.POST['user']
            passwd = request.POST['password']
            type = request.POST['type']
            backnode = BackupServer.objects.get(id=backnode_id)
            backnode.name = name
            backnode.ip = ip
            backnode.port = port
            backnode.user = user
            backnode.passwd = passwd
            backnode.type = type
            backnode.save()
            status = 1
            return render(request, 'bkrs/backnode_edit.html', locals())
        except Exception,e:
            status = 2
            return render(request, 'bkrs/backnode_edit.html', locals())




@login_required
def customer_add(request):
    customer_add_flag = True
    temp_name = 'dbmanage/dbmanage_header.html'
    if request.method == 'POST':
        customers_name = request.form['customers_name']
        customers_short = request.form['customers_short']
        mysqldump_path = request.form['mysqldump_path']
        local_back_dir = request.form['local_back_dir']
        local_save = request.form['local_save']
        db_name = request.form['db_name']

        customer = BackupHostConf.objects.filter(customers_name=customers_name,customers_short=customers_short
                                                 ,dbname=db_name)
        if customer:
            info = '%s平台 添加记录失败,客户名称/数据库名称已存在!' %customers_name
            backhost = BackupHostConf.objects.all()
            return render(request,'bkrs/base.html',locals())

        backhost_id = int(request.form['backhost_id'])
        # random_pass = GenPassword()
        customer = BackupHostConf(customers_name=customers_name,customers_short=customers_short,
                             mysqldump_path=mysqldump_path,local_back_dir=local_back_dir,
                             db_name=db_name if db_name else 'ALL',
                             backhost_id=backhost_id,local_save=local_save)
        customer.save()


        # config_dict = {'apiurl':config_url.value,'apipath':config_apipath.value,'apiport':int(config_apiport.value),
        #                'mysql_dump':mysqldump_path,'mysql_host':db_ip,'mysql_port':db_port,
        #                'mysql_user':db_user,'mysql_pass':db_pass,'database_name':db_name,
        #                'backup_dir':local_back_dir,'customers_user':customers_short,'customers_pass':random_pass,
        #                'CorpID':config_CorpID.value,'Secret':config_Secret.value}
        # print config_dict
        # back_code = open(Config.back_script).read()
        # code_string = string.Template(back_code)
        # pro_code = code_string.substitute(config_dict)
        # scripts_dir = Config.scripts_dir
        # print scripts_dir,customers_short
        # config_file_dir = os.path.join(scripts_dir,customers_short)
        # if not os.path.exists(config_file_dir):
        #     os.mkdir(config_file_dir)
        # customers_back_file = customers_short + '_Backup_Mysql.py'
        # customers_back_file = os.path.join(config_file_dir,customers_back_file)
        # output = open(customers_back_file,'w')
        # output.write(pro_code)
        # output.close()
        # py_compile.compile(customers_back_file)
        return HttpResponse(request.url_root+str('customers_back_file'+'c').split('BackManage')[1])
    else:
        backhost = BackupHostConf.objects.all()
        return render(request, 'bkrs/base.html', locals())

#
# @main.route('/set_config/',methods=['GET', 'POST'])
# # @login_required
# def set_config():
#     if request.method == 'POST':
#         try:
#             apiurl = request.form['apiurl']
#             apipath = request.form['apipath']
#             apiport = request.form['apiport']
#             CorpID = request.form['CorpID']
#             Secret = request.form['Secret']
#             apiurl_obj = config.query.filter_by(key='apiurl').first()
#             apiurl_obj.value = apiurl
#             apipath_obj = config.query.filter_by(key='apipath').first()
#             apipath_obj.value = apipath
#             apiport_obj = config.query.filter_by(key='apiport').first()
#             apiport_obj.value = apiport
#             CorpID_obj = config.query.filter_by(key='CorpID').first()
#             CorpID_obj.value = CorpID
#             Secret_obj = config.query.filter_by(key='Secret').first()
#             Secret_obj.value = Secret
#             db.session.add(apiurl_obj)
#             db.session.add(apipath_obj)
#             db.session.add(apiport_obj)
#             db.session.add(CorpID_obj)
#             db.session.add(Secret_obj)
#             db.session.commit()
#         except Exception as e:
#             print e.message
#             flash(u'系统设置更新失败!')
#             return redirect(url_for('main.set_config'))
#         flash(u'系统设置更新成功!')
#         return redirect(url_for('main.set_config'))
#     else:
#         try:
#             config_url = config.query.filter_by(key='apiurl').first().value
#             config_apipath = config.query.filter_by(key='apipath').first().value
#             config_apiport = config.query.filter_by(key='apiport').first().value
#             config_CorpID = config.query.filter_by(key='CorpID').first().value
#             config_Secret = config.query.filter_by(key='Secret').first().value
#             return render_template('config.html',apiurl=config_url,apipath=config_apipath,apiport=config_apiport,
#                                    CorpID=config_CorpID,Secret=config_Secret)
#         except Exception as e:
#             print e.message
#             return render_template('config.html')
#
#
# @main.route('/api/', methods=['GET', 'POST'])
# def api():
#     if request.method == 'POST':
#        operation = request.form['operation']
#        if operation == 'auth':
#            auth_user = request.form['user']
#            auth_pass = request.form['pass']
#            customer = customers.query.filter(and_(customers.customers_user==auth_user,customers.customers_pass==auth_pass,customers.customers_status==0)).first()
#            if customer:
#                back_host = backhosts.query.filter_by(id=customer.backhost_id).first()
#                data = {'auth':'ok','customer_name':customer.customers_name,'ftp_ip':back_host.ftp_ip,'ftp_port':int(back_host.ftp_port),'local_save':customer.local_save,
#                        'ftp_user':back_host.ftp_user,'ftp_pass':back_host.ftp_pass,'ftp_dir':customer.customers_short}
#                return json.dumps(data)
#        elif operation == 'upload_info':
#            md5 = request.form['md5']
#            customer_short = request.form['name']
#            upload_ip = request.form['upload_ip']
#            upload_path = request.form['upload_path']
#            upload_name = request.form['upload_name']
#            upload_time = request.form['upload_time']
#            upload_size = request.form['upload_file_size']
#            customer = customers.query.filter_by(customers_short=customer_short).first()
#            backarchive = backarchives(customer_id=customer.id,back_name=upload_name,back_ip=upload_ip,back_path=upload_path,
#                                       back_time=upload_time,back_md5=md5,back_size=upload_size)
#            db.session.add(backarchive)
#            db.session.commit()
#            data =  {'backup_info':'ok'}
#            return json.dumps(data)
#     else:
#         data = {'status':'ok'}
#         return json.dumps(data)
#
#
# @main.route('/add_backnode/',methods=['GET', 'POST'])
@login_required
def add_backnode(request):
    add_backnode_flag = True
    temp_name = 'dbmanage/dbmanage_header.html'
    if request.method == 'POST':
        name = request.POST['node_name']
        ip = request.POST['ftp_ip']
        port = request.POST['ftp_port']
        user = request.POST['ftp_user']
        passwd = request.POST['ftp_pass']
        back_node = BackupServer.objects.filter(name=name,ip=ip,port=port)
        if back_node:
            info = '%s 节点已经存在，请勿重复添加!' %name
            return render(request, 'bkrs/base.html', locals())
        back_node = BackupServer(name=name,ip=ip,port=port,user=user,passwd=passwd)
        back_node.save()
        info = '%s 节点添加成功!' %name
        return render(request, 'bkrs/base.html', locals())
    else:
        return render(request, 'bkrs/base.html', locals())

@login_required()
def backnode(request):
    backnode_flag = True
    temp_name = 'dbmanage/dbmanage_header.html'
    if request.method == 'POST':
        pass
    else:
        backnodes = BackupServer.objects.all()
        return render(request, 'bkrs/base.html', locals())

# @main.route('/backmanage/',methods=['GET', 'POST'])
@login_required
def backarchives(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    if request.method == 'POST':
        pass
    else:
        backarchives_flag = True
        backarchive_all = BackupLog.objects.all()
        return render(request,'bkrs/base.html',locals())



@login_required
def backup_statics(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    if request.method == 'POST':
        pass
    else:

        backup_statics_flag = True
        backarchive_all = BackupLog.objects.all()
        return render(request,'bkrs/base.html',locals())


@login_required
def customer(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    customer_flag = True
    if request.method == 'POST':
        try:
            customer_id = request.form['customer_id']
            customer_oper = request.form['customer_oper']
            customer = BackupHostConf.objects.get(id=customer_id)
            if customer_oper == 'stop_back':
                customer.customers_status = 1
            else:
                customer.customers_status = 0
            customer.save()
            return u"更新状态成功！"
        except Exception, e:
            print e
            return u"更新状态失败！"
    else:
        customer_all = BackupHostConf.objects.all()
        return render(request,'bkrs/base.html',locals())

@login_required
def failed_customer(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    backfailed_flag = True
    backfaileds = backfailed.objects.all().order_by('-count_date')
    return render(request, 'bkrs/base.html', locals())


@login_required
def help(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    help_flag = True
    return render(request, 'bkrs/base.html', locals())


@csrf_exempt
@token_verify()
def received_backup_info(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        # hostname = received_json_data["hostname"]
        if received_json_data.has_key('error'):
            try:
                error = received_json_data['error']
                database = received_json_data['database']
                ip = received_json_data['ip']
                port = received_json_data['port']
                instance_id = received_json_data['instance_id']
                db_instance = Db_instance.objects.get(id=int(instance_id))
                backup_type = received_json_data['backup_type']
                begin_backup_time = received_json_data['begin_backup_time']
                bg = backfailed(host=db_instance, ip=ip, port=port, count_date=begin_backup_time,
                                back_type=backup_type, back_failed=1, error='[{0}]--{1}'.format(database,error)
                                )

                bg.save()
            except:

                error = received_json_data['error']
                instance_id = received_json_data['instance_id']
                db_instance = Db_instance.objects.get(id=int(instance_id))
                bg = backfailed(host=db_instance, error=error)
                bg.save()

            return HttpResponse('Error log post ok!')

        else:
            if  received_json_data['backup_type'] == 'mysqldump':
                try:
                    database = received_json_data['database']
                    ip = received_json_data['ip']
                    backup_status = received_json_data['backup_status']
                    backup_path = received_json_data['backup_path']
                    begin_backup_time = received_json_data['begin_backup_time']
                    instance_id = received_json_data['instance_id']
                    backup_type = received_json_data['backup_type']
                    backup_file = received_json_data['backup_file']
                    end_backup_time = received_json_data['end_backup_time']
                    command = received_json_data['command']
                    change_master_to = received_json_data['change_master_to']
                    md5 = received_json_data['md5']
                    port = received_json_data['port']
                    size = received_json_data['size']
                    host = Host.objects.get(ip=ip)
                    db_instance = Db_instance.objects.get(id=int(instance_id))
                    backuplog = BackupLog(host=db_instance, hostname=host.hostname, ip=ip, port=port, type=backup_type,
                                          start_date=begin_backup_time, finish_date=end_backup_time,
                                          master_log_file=change_master_to.split(' ')[4].split('=')[1].split(',')[0],
                                          master_log_pos=change_master_to.split(' ')[5].split('=')[1].split(';')[0],
                                          backup_local_path=backup_path, backup_files=backup_file,
                                          is_tar=1, local_tar_file=backup_path+backup_file, status=backup_status,
                                          local_tar_file_md5=md5, backup_files_size=size, command=command,
                                          database=database,
                                          # remote_tar_file
                                          # verify
                                          # verify_date
                                          # host_id
                                          #
                                          # remote_backup_path
                                          # remote_backup_host_id
                                          # binlog_max_datetime
                                          # binlog_max_pos
                                          # binlog_min_datetime
                                          # binlog_min_pos
                    )

                    backuplog.save()
                except:
                    instance_id = received_json_data['instance_id']
                    db_instance = Db_instance.objects.get(id=int(instance_id))
                    host = Host.objects.get(ip=db_instance.ip)
                    backuplog = BackupLog(host=db_instance, hostname=host.hostname, ip=db_instance.ip, port=db_instance.port,
                                          # verify_date
                                          # host_id
                                          #
                                          # remote_backup_path
                                          # remote_backup_host_id
                                          # binlog_max_datetime
                                          # binlog_max_pos
                                          # binlog_min_datetime
                                          # binlog_min_pos
                                          )
                    backuplog.save()
            if received_json_data['backup_type'] == 'binlog':
                kargs = {}
                try:
                    # database = received_json_data['database']
                    ip = received_json_data['ip']
                    backup_status = received_json_data['backup_status']
                    kargs['backup_status'] = backup_status
                    backup_path = received_json_data['backup_path']
                    kargs['backup_path'] = backup_path
                    begin_backup_time = received_json_data['begin_backup_time']
                    kargs['begin_backup_time'] = begin_backup_time
                    instance_id = received_json_data['instance_id']
                    backup_type = received_json_data['backup_type']
                    kargs['backup_type'] = backup_type
                    backup_file = received_json_data['backup_file']
                    kargs['backup_file'] = backup_file
                    end_backup_time = received_json_data['end_backup_time']
                    kargs['end_backup_time'] = end_backup_time
                    # command = received_json_data['command']
                    # change_master_to = received_json_data['change_master_to']
                    md5 = received_json_data['md5']
                    kargs['md5'] = md5
                    port = received_json_data['port']
                    kargs['port'] = port
                    size = received_json_data['size']
                    kargs['size'] = size
                    host = Host.objects.get(ip=ip)
                    binlog_min_datetime = received_json_data['start_time']
                    kargs['binlog_min_datetime'] = binlog_min_datetime
                    binlog_max_datetime = received_json_data['end_time']
                    kargs['binlog_max_datetime'] = binlog_max_datetime
                    binlog_min_pos = received_json_data['start_pos']
                    kargs['binlog_min_pos'] = binlog_min_pos
                    binlog_max_pos = received_json_data['end_pos']
                    kargs['binlog_max_pos'] = binlog_max_pos
                    db_instance = Db_instance.objects.get(id=int(instance_id))
                    backuplog = BackupLog(host=db_instance, hostname=host.hostname, ip=ip, port=port, type=backup_type,
                                          start_date=begin_backup_time, finish_date=end_backup_time,
                                          # master_log_file=change_master_to.split(' ')[4].split('=')[1].split(',')[0],
                                          # master_log_pos=change_master_to.split(' ')[5].split('=')[1].split(';')[0],
                                          backup_local_path=backup_path, backup_files=backup_file,
                                          is_tar=1, local_tar_file=backup_path + backup_file, status=backup_status,
                                          local_tar_file_md5=md5, backup_files_size=size,
                                          binlog_min_datetime=binlog_min_datetime, binlog_max_datetime=binlog_max_datetime,
                                          binlog_min_pos=binlog_min_pos, binlog_max_pos=binlog_max_pos

                                          # remote_tar_file
                                          # verify
                                          # verify_date
                                          # host_id
                                          #
                                          # remote_backup_path
                                          # remote_backup_host_id
                                          # binlog_max_datetime
                                          # binlog_max_pos
                                          # binlog_min_datetime
                                          # binlog_min_pos
                                          )

                    backuplog.save()
                except Exception,e:
                    instance_id = received_json_data['instance_id']
                    db_instance = Db_instance.objects.get(id=int(instance_id))
                    host = Host.objects.get(ip=db_instance.ip)
                    backuplog = BackupLog(host=db_instance, hostname=host.hostname, ip=db_instance.ip,
                                          port=db_instance.port,error=e,**kargs
                                          # verify_date
                                          # host_id
                                          #
                                          # remote_backup_path
                                          # remote_backup_host_id
                                          # binlog_max_datetime
                                          # binlog_max_pos
                                          # binlog_min_datetime
                                          # binlog_min_pos
                                          )
                    backuplog.save()

            return HttpResponse("Post the backup Data successfully!")
    else:
        if request.GET.has_key('instance_id'):
            pc = prpcrypt()
            try:
                db_instance = Db_instance.objects.get(id=request.GET['instance_id'])
                t = request.GET['t']
                pc.key = t[-16:]
                account = db_instance.db_account_set.get(db_account_role='admin')
                ip = db_instance.ip
                port = db_instance.port
                user = account.user
                password = pc.encrypt(prpcrypt().decrypt(account.passwd))
                database = 'all'
                data = {'ip':ip,'port':port,'user':user,'password':password}
                return HttpResponse(json.dumps(data))

            except:
                return HttpResponse("Your push have errors, Please Check your data!")



