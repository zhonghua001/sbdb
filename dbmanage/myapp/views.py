# -*- coding: utf-8 -*-
import csv
import datetime
import json
from django.utils import timezone
from accounts.permission import permission_verify
from datetime import timedelta,datetime
from decimal import Decimal
from django.core import serializers
# from captcha.fields import CaptchaStore
# from captcha.helpers import captcha_image_url
from django.template.loader import get_template
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import  Group
from cmdb.models import HostGroup,Host
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse, JsonResponse
# from ratelimit.decorators import ratelimit,is_ratelimited
from django.shortcuts import render, render_to_response,redirect,reverse
from django.template.context import RequestContext
from accounts.models import UserInfo
from dbmanage.blacklist import blFunction as bc
from form import AddForm, LoginForm, Logquery, Uploadform, Taskquery, Taskscheduler,AddDBAccount,AddDBAccountSetDB
from dbmanage.myapp.include import function as func, inception as incept, chart, pri, meta, sqlfilter
from dbmanage.myapp.include.scheduled import get_dupreport
from dbmanage.myapp.models import Db_group, Db_name, Db_account, Db_instance, Task,Db_database_permission,Db_database_permission_detail,Instance_account_admin
from dbmanage.myapp.tasks import task_run, sendmail_task, parse_binlog, parse_binlogfirst,d
from include.encrypt import prpcrypt
from include.function import mysql_query as func_mysql_query
from django_celery_beat.models import CrontabSchedule,PeriodicTask,IntervalSchedule
from dbmanage.myapp.tasks import process_runtask

#path='./myapp/include'
#sys.path.insert(0,path)
#import function as func
# Create your views here.
'''
class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)
'''

@login_required(login_url='/accounts/login')
def index(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    data,col = chart.get_main_chart()
    taskdata,taskcol = chart.get_task_chart()
    bingtu = chart.get_task_bingtu()
    inc_data,inc_col = chart.get_inc_usedrate()
    return render(request, 'dbmanage/index.html', {'inc_data':json.dumps(inc_data),'inc_col':json.dumps(inc_col),'bingtu':json.dumps(bingtu),'data':json.dumps(data),'col':json.dumps(col),'taskdata':json.dumps(taskdata),'taskcol':json.dumps(taskcol),'temp_name':temp_name})
    # print json.dumps(bingtu)
    # return render(request, 'include/base.html',{'inc_data':json.dumps(inc_data),'inc_col':json.dumps(inc_col),'bingtu':json.dumps(bingtu),'data':json.dumps(data),'col':json.dumps(col),'taskdata':json.dumps(taskdata),'taskcol':json.dumps(taskcol),'temp_name':temp_name})


@login_required(login_url='/accounts/login/')
def logout(request):
    auth.logout(request)
    response = HttpResponseRedirect("/accounts/login/")
    try:
        response.delete_cookie('myfavword')
    except Exception,e:
        pass
    return response

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_log_query', login_url='/')
@permission_verify()
def log_query(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    #show every dbtags
    #obj_list = func.get_mysql_hostlist(request.user.username,'log')
    #show dbtags permitted to the user
    # obj_list = func.get_mysql_hostlist(request.user.username,'log')
    optype_list = func.get_op_type()
    if request.method == 'POST' :
        form = Logquery(request.POST)
        if form.is_valid():
            begintime = form.cleaned_data['begin']
            endtime = form.cleaned_data['end']
            # hosttag = request.POST['hosttag']
            optype = request.POST['optype']
            data = func.get_log_data(select_group,select_host,optype,begintime,endtime)

            return render(request,'log_query.html',locals())
        else:
            print "not valid"
            return render(request,'log_query.html',locals())
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='query')
        return JsonResponse(db_list, safe=False)
    elif request.GET.has_key('instance_id'):
        return HttpResponse(json.dumps(func.get_hostlist(request, tag='query')))
    else:
        form = Logquery()
        return render(request, 'log_query.html', locals())


@login_required(login_url='/accounts/login/')
@permission_verify()
def mysql_query(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    #print request.user.username
    # print request.user.has_perm('myapp.can_mysql_query')
    try:
        favword = request.COOKIES['myfavword']
    except Exception,e:
        pass
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    # objlist = func.get_mysql_hostlist(request.user.username)
    if request.method == 'POST':
        form = AddForm(request.POST)
        # request.session['myfavword'] = request.POST['favword']
        # choosed_host = request.POST['cx']

        # if not UserInfo.objects.get(username=request.user.username).db_name_set.filter(dbtag=choosed_host)[:1]:
        #     return HttpResponseRedirect("/")

        # if request.POST.has_key('searchdb'):
        #     db_se = request.POST['searchdbname']
        #     objlist_tmp = func.get_mysql_hostlist(request.user.username, 'tag', db_se)
        #     # incase not found any db
        #     if len(objlist_tmp) > 0:
        #         objlist = objlist_tmp

        if form.is_valid():
            a = form.cleaned_data['a']

            # get first valid statement
            try:
                #print func.sql_init_filter(a)
                a = sqlfilter.get_sql_detail(sqlfilter.sql_init_filter(a), 1)[0]
            except Exception, e:
                a='wrong'
                pass
            db_name = request.POST['optionsRadios'].split(':')[1]
            db_account = Db_account.objects.get(id=int(request.POST['optionsRadios'].split(':')[0]))
            try:
                #show explain
                if request.POST.has_key('explain'):
                    a = func.check_explain (a)
                    (data_list,collist,dbname) = func.get_mysql_data(db_account,a,request.user.username,request,100)
                    return render(request, 'mysql_query.html', locals())
                    # return render(request,'mysql_query.html',{'form': form,'objlist':objlist,'data_list':data_list,'collist':collist,'choosed_host':choosed_host,'dbname':dbname})
                    #export csv
                elif request.POST.has_key('export') and request.user.has_perm('myapp.can_export') :
                    # check if table in black list and if user has permit to query

                    inBlackList, blacktb = bc.Sqlparse(a).check_query_table(db_account,request.user.username)
                    if inBlackList:
                        return render(request, 'mysql_query.html', locals())

                    a,numlimit = func.check_mysql_query(a,request.user.username,'export')
                    (data_list,collist,dbname) = func.get_mysql_data(db_account,a,request.user.username,request,numlimit)
                    pseudo_buffer = Echo()
                    writer = csv.writer(pseudo_buffer)
                    #csvdata =  (collist,'')+data_mysql
                    i=0
                    results_long = len(data_list)
                    results_list = [None] * results_long
                    for i in range(results_long):
                        results_list[i] = list(data_list[i])
                    results_list.insert(0,collist)
                    a = u'zhongwen'
                    ul= 1234567L
                    for result in results_list:
                        i=0
                        for item in result:
                            if type(item) == type(a):
                                try:
                                    result[i] = item.encode('gb18030')
                                except Exception,e:
                                    result[i] = item.replace(u'\xa0', u' ').encode('gb18030')
                            elif type(item)==type(ul):
                                try:
                                    result[i] = str(item) + "\t"
                                except Exception,e:
                                    pass
                            i = i + 1
                    response = StreamingHttpResponse((writer.writerow(row) for row in results_list),content_type="text/csv")
                    response['Content-Disposition'] = 'attachment; filename="export.csv"'
                    return response
                elif request.POST.has_key('query'):
                    #check if table in black list and if user has permit to query
                    inBlackList,blacktb = bc.Sqlparse(a).check_query_table(db_account,request.user.username)
                    if inBlackList:
                        return render(request, 'mysql_query.html', locals())
                    #get nomal query
                    a,numlimit = func.check_mysql_query(a,request.user.username)
                    (data_list,collist,dbname) = func.get_mysql_data(db_account,a,request.user.username,request,numlimit)
                    # donot show wrong message sql
                    if a == func.wrong_msg:
                        del a
                    # print choosed_host
                    return render(request, 'mysql_query.html', locals())
                elif request.POST.has_key('sqladvice'):

                    advice = func.get_advice(db_account, a, request)
                    return render(request, 'mysql_query.html', locals())

                return render(request, 'mysql_query.html', locals())

            except Exception,e:
                print e
                return render(request, 'mysql_query.html', locals())
                # return render(request, 'mysql_query.html', {'form': form, 'objlist': objlist})
        else:
            return render(request, 'mysql_query.html', locals())
            # return render(request, 'mysql_query.html', {'form': form,'objlist':objlist})
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='query')
        return JsonResponse(db_list,safe=False)
    elif request.GET.has_key('instance_id'):
        return HttpResponse(json.dumps(func.get_hostlist(request, tag='query')))
    else:

        form = AddForm()
        #
        # try:
        #     favword = request.session['myfavword']
        # except Exception,e:
        #     pass

        return render(request, 'mysql_query.html', locals())
        # return render(request, 'mysql_query.html', {'form': form,'objlist':objlist})



# def mysql_query(request):
#     #print request.user.username
#     # print request.user.has_perm('myapp.can_mysql_query')
#     objlist = func.get_mysql_hostlist(request.user.username)
#     if request.method == 'POST':
#         form = AddForm(request.POST)
#         if form.is_valid():
#             a = form.cleaned_data['a']
#             choosed_host = request.POST['cx']
#             try:
#                 #show explain
#                 if request.POST.has_key('explain'):
#                     a = func.check_explain (a)
#                     (data_list,collist,dbname) = func.get_mysql_data(choosed_host,a,request.user.username,request,100)
#                     return render(request, 'mysql_query.html', locals())
#                     # return render(request,'mysql_query.html',{'form': form,'objlist':objlist,'data_list':data_list,'collist':collist,'choosed_host':choosed_host,'dbname':dbname})
#                     #export csv
#                 elif request.POST.has_key('export'):
#                     a,numlimit = func.check_mysql_query(a,request.user.username,'export')
#                     (data_list,collist,dbname) = func.get_mysql_data(choosed_host,a,request.user.username,request,numlimit)
#                     pseudo_buffer = Echo()
#                     writer = csv.writer(pseudo_buffer)
#                     #csvdata =  (collist,'')+data_mysql
#                     i=0
#                     results_long = len(data_list)
#                     results_list = [None] * results_long
#                     for i in range(results_long):
#                         results_list[i] = list(data_list[i])
#                     results_list.insert(0,collist)
#                     a = u'zhongwen'
#                     for result in results_list:
#                         i=0
#                         for item in result:
#                             if type(item) == type(a):
#                                 result[i] = item.encode('gb2312')
#                             i = i + 1
#                     response = StreamingHttpResponse((writer.writerow(row) for row in results_list),content_type="text/csv")
#                     response['Content-Disposition'] = 'attachment; filename="export.csv"'
#                     return response
#                 elif request.POST.has_key('query'):
#                 #get nomal query
#                     a,numlimit = func.check_mysql_query(a,request.user.username)
#                     # print type(a)
#                     # print a
#                     (data_list,collist,dbname) = func.get_mysql_data(choosed_host,a,request.user.username,request,numlimit)
#                     return render(request, 'mysql_query.html', locals())
#
#                     # return render(request,'mysql_query.html',{'form': form,'objlist':objlist,'data_list':data_list,'collist':collist,'choosed_host':choosed_host,'dbname':dbname})
#             except Exception,e:
#                 print e
#                 return render(request, 'mysql_query.html', locals())
#
#                 # return render(request, 'mysql_query.html', {'form': form, 'objlist': objlist})
#         else:
#             return render(request, 'mysql_query.html', locals())
#
#             # return render(request, 'mysql_query.html', {'form': form,'objlist':objlist})
#     else:
#         form = AddForm()
#         return render(request, 'mysql_query.html', locals())
#
#         # return render(request, 'mysql_query.html', {'form': form,'objlist':objlist})




class Echo(object):
    """An object that implements just the write method of the file-like interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value
'''
def some_streaming_csv_view(request):
    """A view that streams a large CSV file."""
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    data = (["Row {}".format(idx), str(idx)] for idx in range(65536))
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in data),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="test.csv"'
    return response
'''



@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_execview', login_url='/db')
@permission_verify()
def mysql_exec(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    try:
        favword = request.COOKIES['myfavword']
    except Exception,e:
        pass
    #print request.user.username
    # objlist = func.get_mysql_hostlist(request.user.username,'exec')
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    if request.method == 'POST':
        form = AddForm(request.POST)
        # choosed_host = request.POST['cx']
        # if not UserInfo.objects.get(username=request.user.username).db_name_set.filter(dbtag=choosed_host)[:1]:
        #     return HttpResponseRedirect("/")
        # if request.POST.has_key('searchdb'):
        #     db_se = request.POST['searchdbname']
        #     print(form.a)
        #     objlist_tmp = func.get_mysql_hostlist(request.user.username, 'exec', db_se)
        #     # incase not found any db
        #     if len(objlist_tmp) > 0:
        #         objlist = objlist_tmp

        if form.is_valid():
            a = form.cleaned_data['a']
            #try to get the first valid sql
            try:
                a = sqlfilter.get_sql_detail(sqlfilter.sql_init_filter(a), 2)[0]
                # form = AddForm(initial={'a': a})
            except Exception,e:
                a='wrong'
            sql = a
            a = func.check_mysql_exec(a,request)
            #print request.POST
            try:
                db_name = request.POST['optionsRadios'].split(':')[1]
                db_account = Db_account.objects.get(id=int(request.POST['optionsRadios'].split(':')[0]))
                if request.POST.has_key('commit'):
                    (data_mysql,collist,dbname) = func.run_mysql_exec(db_account,a,request.user.username,request)
                elif request.POST.has_key('check'):
                    tar_dbname = request.POST['optionsRadios'].split(':')[1]
                    data_mysql,collist,dbname = incept.inception_check(tar_dbname,db_account,a)
                # return render(request,'mysql_exec.html',{'form': form,'objlist':objlist,'data_mysql':data_mysql,'collist':collist,'choosed_host':choosed_host,'dbname':dbname})

                return render(request, 'mysql_exec.html', locals())
            except Exception,e:
                return render(request, 'mysql_exec.html', locals())
        else:
            return render(request, 'mysql_exec.html', locals())

            # return render(request, 'mysql_exec.html', {'form': form,'objlist':objlist})

    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='exec')
        return JsonResponse(db_list, safe=False)
    elif request.GET.has_key('instance_id'):
        return HttpResponse(json.dumps(func.get_hostlist(request, tag='exec')))
    else:
        form = AddForm()
        return render(request, 'mysql_exec.html', locals())

        # return render(request, 'mysql_exec.html', {'form': form,'objlist':objlist})



#
# def mysql_exec(request):
#     #print request.user.username
#     obj_list = func.get_mysql_hostlist(request.user.username,'exec')
#     if request.method == 'POST':
#         form = AddForm(request.POST)
#         if form.is_valid():
#             a = form.cleaned_data['a']
#             c = request.POST['cx']
#             a = func.check_mysql_exec(a,request)
#             #print request.POST
#             if request.POST.has_key('commit'):
#                 (data_mysql,collist,dbname) = func.run_mysql_exec(c,a,request.user.username,request)
#             elif request.POST.has_key('check'):
#                 data_mysql,collist,dbname = incept.inception_check(c,a)
#             return render(request,'mysql_exec.html',{'form': form,'objlist':obj_list,'data_list':data_mysql,'col':collist,'choosed_host':c,'dbname':dbname})
#
#         else:
#             return render(request, 'mysql_exec.html', {'form': form,'objlist':obj_list})
#     else:
#         form = AddForm()
#         return render(request, 'mysql_exec.html', {'form': form,'objlist':obj_list})




@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_inception', login_url='/')
@permission_verify()
def inception(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    # objlist = func.get_mysql_hostlist(request.user.username,'incept')
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    if request.method == 'POST':
        # if request.POST.has_key('searchdb'):
        #     db_se = request.POST['searchdbname']
        #     # objlist_tmp = func.get_mysql_hostlist(request.user.username, 'incept', db_se)
        #     # incase not found any db
        #     if len(objlist_tmp) > 0:
        #         # objlist = objlist_tmp

        specification = request.POST['specification'][0:30]
        db_name = request.POST['optionsRadios'].split(':')[1]
        db_account = Db_account.objects.get(id=int(request.POST['optionsRadios'].split(':')[0]))
        if request.POST.has_key('check'):
            form = AddForm(request.POST)
            upform = Uploadform()

            if form.is_valid():
                a = form.cleaned_data['a']

                # choosed_host = request.POST['cx']
                # get valid statement
                try:
                    tmpsqltext = ''
                    for i in sqlfilter.get_sql_detail(sqlfilter.sql_init_filter(a), 2):
                        tmpsqltext = tmpsqltext + i
                    a = tmpsqltext
                    form = AddForm(initial={'a': a})
                except Exception, e:
                    pass
                tar_dbname = request.POST['optionsRadios'].split(':')[1]
                data_mysql, collist, dbname = incept.inception_check(tar_dbname,db_account,a,2)
                #check the nee to split sqltext first
                if len(data_mysql)>1:
                    split = 1
                    return render(request, 'inception.html', locals())
                else:
                    tar_dbname = request.POST['optionsRadios'].split(':')[1]
                    data_mysql,collist,dbname = incept.inception_check(tar_dbname,db_account,a)
                    return render(request, 'inception.html', locals())
            else:
                # print "not valid"
                return render(request, 'inception.html', locals())
        elif request.POST.has_key('upload') and request.FILES.has_key('filename'):

            upform = Uploadform(request.POST,request.FILES)
            #c = request.POST['cx']
            if upform.is_valid():
                # choosed_host = request.POST['cx']
                sqltext=''
                for chunk in request.FILES['filename'].chunks():
                    #print chunk
                    try:
                        chunk = chunk.decode('utf8')
                    except Exception,e:
                        chunk = chunk.decode('gbk')
                    sqltext = sqltext + chunk
                # get valid statement
                try:
                    tmpsqltext=''
                    for i in  sqlfilter.get_sql_detail(sqlfilter.sql_init_filter(sqltext), 2):
                        tmpsqltext=tmpsqltext + i
                    sqltext = tmpsqltext
                except Exception, e:
                    pass
                form = AddForm(initial={'a': sqltext})
                return render(request, 'inception.html', locals())
            else:
                form = AddForm()
                upform = Uploadform()
                return render(request, 'inception.html', locals())
        elif request.POST.has_key('addtask'):
            form = AddForm(request.POST)
            needbackup = (int(request.POST['ifbackup']) if int(request.POST['ifbackup']) in (0,1) else 1)

            # choosed_host = request.POST['cx']
            upform = Uploadform()

            if form.is_valid():
                sqltext = form.cleaned_data['a']
                # get valid statement
                try:
                    tmpsqltext = ''
                    for i in sqlfilter.get_sql_detail(sqlfilter.sql_init_filter(sqltext), 2):
                        tmpsqltext = tmpsqltext + i
                    sqltext = tmpsqltext
                    form = AddForm(initial={'a': sqltext})
                except Exception, e:
                    pass
                tar_dbname = request.POST['optionsRadios'].split(':')[1]
                data_mysql, tmp_col, dbname = incept.inception_check(tar_dbname,db_account,sqltext, 2)
                # check if the sqltext need to be splited before uploaded
                if len(data_mysql)>1:
                    split = 1
                    status = 'UPLOAD TASK FAIL'
                    return render(request, 'inception.html',locals())
                #check sqltext before uploaded
                else:
                    tar_dbname = request.POST['optionsRadios'].split(':')[1]
                    tmp_data, tmp_col, dbname = incept.inception_check(tar_dbname,db_account,sqltext)
                    for i in tmp_data:
                        if int(i[2]) !=0:
                            result = -1
                            status = 'UPLOAD TASK FAIL,CHECK NOT PASSED'
                            return render(request, 'inception.html',locals())
                myNewTask = incept.record_task(request,sqltext, db_account.instance.ip+':'+db_account.instance.port,db_account.db_account_role,
                                               dbname,'Normal Execute: '+specification,needbackup)
                status='UPLOAD TASK OK'
                # sendmail_task.delay(choosed_host+'\n'+sqltext)
                sendmail_task.delay(myNewTask.id)

                return render(request, 'inception.html', locals())
            else:
                status='UPLOAD TASK FAIL'
                return render(request, 'inception.html', locals())
        elif request.POST.has_key('addtask_force'):
            form = AddForm(request.POST)
            needbackup = (int(request.POST['ifbackup']) if int(request.POST['ifbackup']) in (0, 1) else 1)

            # choosed_host = request.POST['cx']
            upform = Uploadform()

            if form.is_valid():
                sqltext = form.cleaned_data['a']
                # get valid statement
                try:
                    tmpsqltext = ''
                    for i in sqlfilter.get_sql_detail(sqlfilter.sql_init_filter(sqltext), 2):
                        tmpsqltext = tmpsqltext + i
                    sqltext = tmpsqltext
                    form = AddForm(initial={'a': sqltext})
                except Exception, e:
                    pass
                tar_dbname = request.POST['optionsRadios'].split(':')[1]
                data_mysql, tmp_col, dbname = incept.inception_check(tar_dbname, db_account, sqltext, 2)
                # check if the sqltext need to be splited before uploaded
                if len(data_mysql) > 1:
                    split = 1
                    status = 'UPLOAD TASK FAIL'
                    return render(request, 'inception.html', locals())
                # check sqltext before uploaded
                else:
                    tar_dbname = request.POST['optionsRadios'].split(':')[1]
                    tmp_data, tmp_col, dbname = incept.inception_check(tar_dbname, db_account, sqltext)
                    for i in tmp_data:
                        if int(i[2]) not in [0,1]:
                            result = -1
                            status = 'UPLOAD TASK FAIL,CHECK NOT PASSED'
                            return render(request, 'inception.html', locals())
                myNewTask = incept.record_task(request,sqltext, db_account.instance.ip+':'+db_account.instance.port,db_account.db_account_role,
                                               dbname,'Force Execute: '+specification,needbackup)
                status = 'UPLOAD TASK OK'
                # sendmail_task.delay(choosed_host+'\n'+sqltext)
                sendmail_task.delay(myNewTask.id)

                return render(request, 'inception.html', locals())
            else:
                status = 'UPLOAD TASK FAIL'
                return render(request, 'inception.html', locals())
        form = AddForm()
        upform = Uploadform()
        return render(request, 'inception.html', locals())
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='query')
        return JsonResponse(db_list, safe=False)
    elif request.GET.has_key('instance_id'):
        return HttpResponse(json.dumps(func.get_hostlist(request, tag='query')))
    else:
        form = AddForm()
        upform = Uploadform()
        return render(request, 'inception.html', locals())


# @ratelimit(key=func.my_key,method='POST', rate='5/15m')
# def login(request):
#     was_limited = getattr(request, 'limited', False)
#     if was_limited:
#         form = LoginForm()
#
#         error = 1
#         return render_to_response('login.html', RequestContext(request, {'form': form,
#
#                                                                          'error':error}))
#     else:
#         if request.user.is_authenticated():
#             return render(request, 'include/base.html')
#
#         elif  request.method == "POST":
#             form = LoginForm(request.POST)
#             if form.is_valid():
#                 username = form.cleaned_data['username']
#                 password = form.cleaned_data['password']
#                 user = auth.authenticate(username=username, password=password)
#                 if user is not None and user.is_active:
#                     auth.login(request, user)
#                     func.log_userlogin(request)
#                     return HttpResponseRedirect("/")
#                 else:
#                     #login failed
#                     func.log_loginfailed(request, username)
#                     #request.session["wrong_login"] =  request.session["wrong_login"]+1
#                     return render(request,'login.html', {'form': form,'password_is_wrong':True})
#             else:
#                 return render_to_response('login.html', RequestContext(request, {'form': form}))
#         else:
#                 #cha_error
#             form = LoginForm(request.POST)
#
#             chaerror = 1
#             return render(request, 'login.html', {'form': form,'myform':myform,'chaerror':chaerror})
#
#
#



#
# @login_required(login_url='/accounts/login/')
# def upload_file(request):
#     if request.method == "POST":
#         form = Uploadform(request.POST,request.FILES)
#         if form.is_valid():
#         #username = request.user.username
#             username ='test'
#             filename = form.cleaned_data['filename']
#             myfile = Upload()
#             myfile.username = username
#             myfile.filename = filename
#             myfile.save()
#             print myfile.filename.url
#             print myfile.filename.path
#             print myfile.filename.name
#             print ""
#             for chunk in request.FILES['filename'].chunks():
#                 sqltext = sqltext + chunk
#             print sqltext
#             f = open(myfile.filename.path,'r')
#             result = list()
#             for line in f.readlines():
#                 #print line
#                 result.append(line)
#             print "what the fuck"
#             print result
#             return HttpResponse('upload ok!')
#         else :
#             return HttpResponse('upload false!')
#     else:
#         form = Uploadform()
#         return  render(request, 'upload.html', {'form': form})


@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_taskview', login_url='/')
@permission_verify()
def change_task_period(request):

    try:
        taskid = int(request.POST['taskid'])
        period_date = datetime.datetime.utcfromtimestamp(int(request.POST['period_date'][:-3])).replace(tzinfo=timezone.utc)
        task = Task.objects.get(id=taskid)
        if task.status != 'executed' and task.status != 'running' and task.status != 'NULL':
            # db_account = Db_account.objects.get(instance__ip=task.instance.split(':')[0],instance__port=task.instance.split(':')[1],db_account_role=task.db_account_role)
            db_tag = task.instance + '__' + task.db_account_role
            tar_dbname = task.dbtag
            sql = task.sqltext
            mycreatetime = task.create_time
            incept.log_incep_op(sql, tar_dbname, db_tag, request, mycreatetime)
            status = 'appoint'
            task.status = status
            task.operator = request.user.username
            task.update_time = timezone.now()
            task.sche_time = period_date
            task.save()
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=period_date.minute,
                hour=period_date.hour,
                day_of_week='*',
                day_of_month=period_date.day,
                month_of_year=period_date.month,
            )
            if PeriodicTask.objects.filter(task='dbmanage.myapp.tasks.process_runtask',
                                           args='[{}]'.format(taskid)).exists():
                PeriodicTask.objects.filter(task='dbmanage.myapp.tasks.process_runtask',
                                            args='[{}]'.format(taskid)).update(enabled=False)

            PeriodicTask.objects.create(
                crontab=schedule,
                name='Importing contacts ' + str(task.id) + period_date.strftime('%Y-%m-%d %H:%M'),
                task='dbmanage.myapp.tasks.process_runtask',
                args=json.dumps([taskid]),
                expires=period_date + timedelta(seconds=1800)
            )
            result = 'success'
            return HttpResponse(result)
        elif task.status == 'NULL':
            return HttpResponse('PLEASE CHECK THE SQL FIRST')
        else:
            return HttpResponse('Already executed or in running')
    except Exception,e:
        result = e
        return HttpResponse(result)






@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_taskview', login_url='/')
@permission_verify()
def get_rollback(request):
    idnum = request.GET['taskid']
    if request.user.username == Task.objects.get(id=idnum).user:
        sqllist = incept.rollback_sqllist(idnum)
    # print sqllist
    return HttpResponse(json.dumps(sqllist), content_type='application/json')

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_taskview', login_url='/')
@permission_verify()
def get_single_rollback(request):
    sequence = request.GET['sequenceid']
    sqllist = incept.rollback_sql(sequence)
    return HttpResponse(json.dumps(sqllist), content_type='application/json')

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_taskview', login_url='/')
@permission_verify()
def task_manager(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    #obj_list = func.get_mysql_hostlist(request.user.username,'log')
    # obj_list = ['all'] + func.get_mysql_hostlist(request.user.username,'incept')
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    if request.method == 'POST' :
        # request.POST['instance_id'] = select_host
        # hostlist =  HttpResponse(json.dumps(func.get_hostlist(request, tag='log')))
        form = Taskquery(request.POST)
        form2 = Taskscheduler(request.POST)
        if form.is_valid():
            endtime = form.cleaned_data['end']
        else:
            endtime = timezone.now()
        if form2.is_valid():
            sche_time = form2.cleaned_data['sche_time']
            # print sche_time
        else:
            sche_time = timezone.now()
        # db_name = request.POST['optionsRadios'].split(':')[1]
        # db_account = Db_account.objects.get(id=int(request.POST['optionsRadios'].split(':')[0]))
        hosttag = request.POST.get('ins_set') if request.POST.has_key('ins_set') else 0
        data = incept.get_task_list(hosttag, request, endtime)
        if request.POST.has_key('commit'):
            # data = incept.get_task_list(hosttag,request,endtime)
            return render(request,'task_manager.html',{'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        if request.POST.has_key('commit_all'):
        # data = incept.get_task_list(hosttag,request,endtime)
            data = incept.get_task_list(0, request, endtime)
            return render(request,'task_manager.html',{'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})

        elif request.POST.has_key('delete') and (request.user.has_perm('myapp.can_admin_task') or request.user.has_perm('myapp.can_delete_task')):
            id = int(request.POST['delete'])
            nllflag = incept.delete_task(id)
            return render(request,'task_manager.html',{'nllflag':nllflag,'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        elif request.POST.has_key('check'):
            id = int(request.POST['check'])
            results,col,tar_dbname = incept.task_check(id,request)
            return render(request,'task_manager.html',{'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'result':results,'col':col,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        elif request.POST.has_key('see_running'):
            id = int(request.POST['see_running'])
            request.session['recent_taskid'] = id
            results,cols = incept.task_running_status(id)
            return render(request,'task_manager.html',{'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'result_status':results,'cols':cols,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        elif request.POST.has_key('exec') and request.user.has_perm('myapp.can_admin_task'):
            id = int(request.POST['exec'])
            nllflag = task_run(id,request)
            #nllflag = task_run.delay(id)
            # print nllflag
            return render(request,'task_manager.html',{'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'nllflag':nllflag,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        elif request.POST.has_key('stop') and request.user.has_perm('myapp.can_admin_task'):
            sqlsha = request.POST['stop']
            # incept.incep_stop(sqlsha,request)
            results,cols  = incept.incep_stop(sqlsha,request)
            return render(request,'task_manager.html',{'form':form,'form2':form2,'datalist':data,'choosed_host':hosttag,'result_status':results,'cols':cols,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        elif request.POST.has_key('appoint') and request.user.has_perm('myapp.can_admin_task'):
            id = int(request.POST['appoint'])
            incept.set_schetime(id,sche_time)
            return render(request, 'task_manager.html',{'form': form,'form2':form2, 'datalist': data, 'choosed_host': hosttag,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})
        elif request.POST.has_key('update'):
            id = int(request.POST['update'])

            # response = HttpResponseRedirect("/update_task/")
            # response.set_cookie('update_taskid',id)
            # return response

            request.session['update_taskid']=id
            return HttpResponseRedirect("/dbmanage/update_task/")
        elif request.POST.has_key('export_task'):
            task_id_list = request.POST.getlist('choosedlist')
            charset = request.POST['charset']
            data_list = Task.objects.filter(id__in= task_id_list)
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            results_list = []
            a = u'zhongwen'
            for i in data_list:
                if type(i.sqltext) == type(a):
                    if charset =="GB18030":
                        results_list.append([i.id,i.dbtag,i.sqltext.encode('gb18030')])
                    elif charset=="UTF8":
                        results_list.append([i.id, i.dbtag, i.sqltext.encode('utf8')])

            response = StreamingHttpResponse((writer.writerow(row) for row in results_list), content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="task_export.csv"'
            return response
        else:
            return HttpResponseRedirect("/")

    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='log')
        return JsonResponse(db_list, safe=False)

    else:
        data = incept.get_task_list(0,request,timezone.now())
        form = Taskquery()
        form2 = Taskscheduler()
        return render(request, 'task_manager.html', {'form':form,'form2':form2,'datalist':data,'temp_name':temp_name,'host_group':host_group,'select_group':select_group,'select_host':select_host})

#test

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_taskview', login_url='/')
@permission_verify()
def update_task(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    try:
        # id = int(request.COOKIES["update_taskid"])
        id = request.session['update_taskid']
        data = incept.get_task_forupdate(id)
        db_name = data.dbtag
        instance = Db_instance.objects.get(ip=data.instance.split(':')[0], port=data.instance.split(':')[1])
        db_account = Db_account.objects.get(instance=instance, db_account_role=data.db_account_role)
        if select_host == 0 :
            select_host = instance.id
        if select_group == 0 :
            select_group = Host.objects.get(ip=instance.ip).group_id

    except Exception,e:
        str = "ERROR! ID NOT EXISTS , PLEASE CHECK !"
        #return render(request, 'update_task.html', {'str': str})
        return render(request, 'update_task.html', locals())
    # objlist = func.get_mysql_hostlist(request.user.username, 'incept')
    if request.method == 'POST':
        if request.POST.has_key('update'):
            needbackup = (int(request.POST['ifbackup']) if int(request.POST['ifbackup']) in (0,1,2) else 1)

            #update task function can't change db
            flag,str = incept.check_task_status(id)
            if flag:
                sqltext = request.POST['sqltext']
                specify = request.POST['specify'][0:30]
                try:
                    mystatus = request.POST['status']
                except Exception,e:
                    mystatus = data.status
                # choosed_host = data.dbtag
                # data_mysql, tmp_col, dbname = incept.inception_check(choosed_host, sqltext, 2)
                #
                # # check if the sqltext need to be splited before uploaded
                # if len(data_mysql) > 1:
                #     str = 'SPLICT THE SQL FIRST'
                #     return render(request, 'update_task.html', {'str': str})
                # # check sqltext before uploaded
                # else:
                #     tmp_data, tmp_col, dbname = incept.inception_check(choosed_host, sqltext)
                #     for i in tmp_data:
                #         if int(i[2]) != 0:
                #             str = 'UPDATE TASK FAIL,CHECK NOT PASSED'
                #             return render(request, 'update_task.html', {'str': str})
                incept.update_task(id, sqltext, specify,mystatus,needbackup,request.user.username)
                return HttpResponseRedirect("/dbmanage/task/")
            else:
                # return render(request, 'update_task.html', {'str': str})
                return render(request, 'update_task.html', {'temp_name':temp_name,'str': str})
        elif request.POST.has_key('new_task'):
            #new_task can only change the dbtag
            needbackup = (int(request.POST['ifbackup']) if int(request.POST['ifbackup']) in (0,1) else 1)

            choosed_host = request.POST['hosttag']
            if data.dbtag == choosed_host:
                str = 'DB HASN\'T CHANGED! CAN\'T CREATE NEW!'
                return render(request, 'update_task.html', {'str': str})
            data_mysql, tmp_col, dbname = incept.inception_check(choosed_host, data.sqltext, 2)

            # check if the sqltext need to be splited before uploaded
            if len(data_mysql) > 1:
                str = 'SPLICT THE SQL FIRST'
                return render(request, 'update_task.html', {'str': str})
            # check sqltext before uploaded
            else:
                tmp_data, tmp_col, dbname = incept.inception_check(choosed_host, data.sqltext)
                for i in tmp_data:
                    if int(i[2]) != 0:
                        str = 'CREATE NEW TASK FAIL,CHECK NOT PASSED'
                        return render(request, 'update_task.html', {'str': str})
            myNewTask = incept.record_task(request, data.sqltext, choosed_host, data.specification,needbackup)
            # sendmail_task.delay(choosed_host + '\n' + data.sqltext)
            sendmail_task.delay(myNewTask.id)
            return HttpResponseRedirect("/task/")

        # elif request.POST.has_key('searchdb'):
        #     db_se = request.POST['searchname']
        #     objlist = func.get_mysql_hostlist(request.user.username, 'incept',db_se)
        #     if len(objlist) == 0 :
        #         objlist = [data.dbtag,]
        #     return render(request, 'update_task.html', locals())

    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='exec')
        return JsonResponse(db_list, safe=False)
    elif request.GET.has_key('instance_id'):
        return HttpResponse(json.dumps(func.get_hostlist(request, tag='exec')))
    else:
        return render(request, 'update_task.html', locals())



# def update_task(request):
#     try:
#         # id = int(request.COOKIES["update_taskid"])
#         id = request.session['update_taskid']
#     except Exception,e:
#         str = "ERROR"
#         #return render(request, 'update_task.html', {'str': str})
#         return render(request, 'update_task.html', locals())
#     if request.method == 'POST':
#         if request.POST.has_key('update'):
#             flag,str = incept.check_task_status(id)
#             if flag:
#                 sqltext = request.POST['sqltext']
#                 specify = request.POST['specify'][0:30]
#                 mystatus = request.POST['status']
#                 incept.update_task(id, sqltext, specify,mystatus)
#                 return HttpResponseRedirect("/task/")
#             else:
#                 # return render(request, 'update_task.html', {'str': str})
#                 return render(request, 'update_task.html', locals())
#         elif request.POST.has_key('new_task'):
#             pass
#     else:
#         try:
#             data = incept.get_task_forupdate(id)
#             # return render(request, 'update_task.html', {'data': data})
#             return render(request, 'update_task.html', locals())
#         except Exception,e:
#             str = "ID NOT EXISTS , PLEASE CHECK !"
#             # return render(request, 'update_task.html', {'str': str})
#             return render(request, 'update_task.html', locals())



@login_required(login_url='/accounts/login/')
@permission_verify()
def pre_query(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    # if request.user.has_perm('myapp.can_query_pri') or request.user.has_perm('myapp.can_set_pri') :
    if 1 == 1:
        objlist = func.get_mysql_hostlist(request.user.username,'log')
        usergroup = Db_group.objects.all().order_by('groupname')
        inslist = Db_instance.objects.filter(role__in=['read','write','all']).order_by('ip')
        if request.method == 'POST':
            if request.POST.has_key('queryuser'):
            # if request.POST.has_key('accountname') and request.POST['accountname']!='':
                try:
                    username = request.POST['accountname']
                    dbgp, usergp = func.get_user_grouppri(username)

                    pri = func.get_privileges(username)
                    profile = []
                    try:
                        profile = UserInfo.objects.get(username=username).user_profile
                    except Exception,e:
                        pass
                    userdblist,info = func.get_user_pre(username,request)
                    ur = UserInfo.objects.get(username=username)
                    return render(request, 'previliges/prequery.html', {'inslist':inslist,'pri':pri, 'profile':profile, 'dbgp':dbgp, 'usergp':usergp, 'objlist':objlist, 'userdblist': userdblist, 'info':info, 'usergroup':usergroup,'ur':ur,'temp_name':temp_name})
                except Exception,e:
                    return render(request, 'previliges/prequery.html', {'inslist':inslist,'objlist':objlist, 'usergroup':usergroup,'temp_name':temp_name})
            elif request.POST.has_key('querydb'):
                try:
                    choosed_host = request.POST['cx']
                    data,instance,acc,gp = func.get_pre(choosed_host)
                    return render(request, 'previliges/prequery.html', {'inslist':inslist,'objlist':objlist, 'choosed_host':choosed_host, 'data_list':data, 'ins_list':instance, 'acc':acc,'gp':gp, 'usergroup':usergroup,'temp_name':temp_name})
                except Exception, e:
                    return render(request, 'previliges/prequery.html', {'inslist':inslist,'objlist': objlist, 'usergroup': usergroup,'temp_name':temp_name})
            elif request.POST.has_key('querygp'):
                try:
                    choosed_gp = request.POST['choosed_gp']
                    dbgroup = func.get_groupdb(choosed_gp)
                    return render(request, 'previliges/prequery.html', {'inslist':inslist,'objlist': objlist, 'dbgroup':dbgroup, 'usergroup': usergroup,'temp_name':temp_name})
                except Exception,e:
                    return render(request, 'previliges/prequery.html', {'inslist':inslist,'objlist': objlist, 'usergroup': usergroup,'temp_name':temp_name})
            elif request.POST.has_key('queryins'):
                try:
                    insname = Db_instance.objects.get(id=int(request.POST['ins_set']))
                    tmpli = []
                    for i in insname.db_name_set.all():
                        for x in i.instance.all():
                            tmpli.append(int(x.id))
                    tmpli = list(set(tmpli))
                    bro = Db_instance.objects.filter(id__in=tmpli)
                    return render(request, 'previliges/prequery.html', locals())
                except Exception,e:
                    return render(request, 'previliges/prequery.html', locals())

        else:
            return render(request, 'previliges/prequery.html', locals())
    else:
        return HttpResponseRedirect("/")



# @permission_required('myapp.can_set_pri', login_url='/')
@login_required(login_url='/accounts/login/')
@permission_verify()
def pre_set(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    userlist,grouplist = func.get_UserAndGroup()
    usergroup=func.get_usergp_list()
    dblist = Db_name.objects.all().order_by('dbtag')
    public_user = func.public_user
    if request.method == 'POST':
        username = request.POST['account']
        if request.POST.has_key('set'):
            try :
                dbgplist = request.POST.getlist('choosedlist')
                group = request.POST.getlist('user_group')
                ch_db = request.POST.getlist('user_dblist')
                #change username or password
                new_username = request.POST['newname']
                new_passwd = request.POST['newpasswd']
                mail = request.POST['newmail']
                if len(new_username)>0:
                    tmp = UserInfo.objects.get(username=username)
                    tmp.username = new_username
                    tmp.save()
                    username = new_username
                if len(new_passwd)>0:
                    tmp = UserInfo.objects.get(username=username)
                    tmp.set_password(new_passwd)
                    tmp.save()
                # if len(new_mail) > 0:
                #update mail

                tmp = UserInfo.objects.get(username=username)
                tmp.email = mail
                tmp.save()

                func.clear_userpri(username)
                func.set_groupdb(username,dbgplist)
                user = UserInfo.objects.get(username=username)
                func.set_usergroup(user, group)
                func.set_user_db(user, ch_db)
                info = 'SET USER ' + username + '  OK!'
                userlist = UserInfo.objects.exclude(username=public_user).order_by('username')
                return render(request, 'previliges/pre_set.html', {'mail':mail,'username':username,'info':info, 'dblist':dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup':usergroup,'temp_name':temp_name})
            except Exception,e:
                info = 'SET USER ' + username + '  FAILED!'
                return render(request, 'previliges/pre_set.html', {'info':info, 'dblist':dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup':usergroup,'temp_name':temp_name})
        elif request.POST.has_key('reset'):
            func.clear_userpri(username)
            info = 'RESET USER '+ username + '  OK!'
            return render(request, 'previliges/pre_set.html', {'info':info, 'dblist':dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup':usergroup,'temp_name':temp_name})
        elif request.POST.has_key('query'):
            try:
                dbgp,usergp = func.get_user_grouppri(username)
                userdblist,info = func.get_user_pre(username, request)
                mail = UserInfo.objects.get(username = username).email
                return render(request, 'previliges/pre_set.html', {'mail':mail,'username':username, 'dbgp':dbgp, 'usergp':usergp, 'userdblist':userdblist, 'dblist':dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup':usergroup,'temp_name':temp_name})
            except Exception,e:
                return render(request, 'previliges/pre_set.html',{'dblist': dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup': usergroup,'temp_name':temp_name})

        elif request.POST.has_key('delete'):
            try:
                info = 'DELETE USER ' + username + '  OK!'
                func.delete_user(username)
                userlist = UserInfo.objects.exclude(username=public_user)
                return render(request, 'previliges/pre_set.html',{'info': info, 'dblist': dblist, 'userlist': userlist, 'grouplist': grouplist,'usergroup': usergroup,'temp_name':temp_name})
            except Exception,e:
                info = 'DELETE USER ' + username + '  FAILED!'
                return render(request, 'previliges/pre_set.html', {'info': info, 'dblist': dblist, 'userlist': userlist, 'grouplist': grouplist,'usergroup': usergroup,'temp_name':temp_name})
        elif  request.POST.has_key('create'):
            try:
                username = request.POST['newname']
                passwd = request.POST['newpasswd']
                mail = request.POST['newmail']
                group = request.POST.getlist('user_group')
                dbgplist = request.POST.getlist('choosedlist')
                ch_db = request.POST.getlist('user_dblist')
                user = func.create_user(username,passwd,mail)
                func.set_groupdb(username, dbgplist)
                func.set_user_db(user, ch_db)
                func.set_usergroup(user,group)
                info = "CREATE USER SUCCESS!"
                userlist = UserInfo.objects.exclude(username=public_user).order_by('username')
                return render(request, 'previliges/pre_set.html', {'user':user,'info':info, 'dblist':dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup':usergroup,'temp_name':temp_name})
            except Exception,e:
                info = "CREATE USER FAILED!"
                return render(request, 'previliges/pre_set.html', {'info':info, 'dblist':dblist, 'userlist': userlist, 'grouplist': grouplist, 'usergroup':usergroup,'temp_name':temp_name})
    else:
        pri.init_ugroup
        return render(request, 'previliges/pre_set.html', {'dblist':dblist, 'userlist':userlist, 'grouplist':grouplist, 'usergroup':usergroup,'temp_name':temp_name})


@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def set_dbgroup(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    public_user = func.public_user
    dbgrouplist,userlist,dbnamelist = pri.get_full()
    if request.method == 'POST':
        if request.POST.has_key('query'):
            try:
                groupname = request.POST['dbgroup_set']
                s_dbnamelist,s_userlist = pri.get_group_detail(groupname)
                return render(request, 'previliges/db_group.html', locals())
            except Exception,e:
                return render(request, 'previliges/db_group.html', locals())
        elif request.POST.has_key('create'):
            try:
                info = "CREATE OK!"
                groupname = request.POST['newname']
                dbnamesetlist = request.POST.getlist('dbname_set')
                usersetlist = request.POST.getlist('user_set')
                s_dbnamelist,s_userlist = pri.create_dbgroup(groupname,dbnamesetlist,usersetlist)
                return render(request, 'previliges/db_group.html', locals())
            except Exception,e:
                info = "CREATE FAILED!"
                return render(request, 'previliges/db_group.html', locals())
        elif request.POST.has_key('set'):
            try:
                info = "SET OK!"
                groupname = request.POST['dbgroup_set']
                new_groupname = request.POST['newname']
                a =request.POST.getlist('dbname_set')
                b =  request.POST.getlist('user_set')
                #rename group name
                if len(groupname)>0:
                    tmp = Db_group.objects.get(groupname=groupname)
                    tmp.groupname = new_groupname
                    tmp.save()
                    groupname = new_groupname

                s_dbnamelist, s_userlist = pri.set_dbgroup(groupname, a, b)
                return render(request, 'previliges/db_group.html', locals())
            except Exception,e:
                info = "SET FAILED"
                return render(request, 'previliges/db_group.html', locals())

        elif request.POST.has_key('delete'):
            try:
                info = "DELETE OK!"
                groupname = request.POST['dbgroup_set']
                pri.del_dbgroup(groupname)
                return render(request, 'previliges/db_group.html', locals())
            except Exception,e:
                info = "DELETE FAILED!"
                return render(request, 'previliges/db_group.html', locals())
    else:
        return render(request,'previliges/db_group.html',locals())

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def set_ugroup(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    public_user = func.public_user
    grouplist, perlist,userlist = pri.get_full_per()
    if request.method == 'POST':
        if request.POST.has_key('query'):
            try:
                groupname = request.POST['group_set']
                s_perlist,s_userlist = pri.get_ugroup_detail(groupname)
                return render(request, 'previliges/u_group.html', locals())
            except Exception,e:
                return render(request, 'previliges/u_group.html', locals())
        elif request.POST.has_key('create'):
            try:
                info = "CREATE OK!"
                groupname = request.POST['newname']
                persetlist = request.POST.getlist('per_set')
                usersetlist = request.POST.getlist('user_set')
                s_perlist,s_userlist = pri.create_ugroup(groupname,persetlist,usersetlist)
                return render(request, 'previliges/u_group.html', locals())
            except Exception,e:
                info = "CREATE FAILED!"
                return render(request, 'previliges/u_group.html', locals())
        elif request.POST.has_key('delete'):
            try:
                groupname = request.POST['group_set']
                info = "DELETE OK!"
                pri.del_ugroup(groupname)
                return render(request, 'previliges/u_group.html', locals())
            except Exception,e:
                info = "DELETE FAILED!"
                return render(request, 'previliges/u_group.html', locals())
        elif request.POST.has_key('set'):
            try:
                info = "SET OK!"
                groupname = request.POST['group_set']
                #rename group
                new_groupname = request.POST['newname']
                if len(new_groupname)>0:
                    tmp = Group.objects.get(name=groupname)
                    tmp.name = new_groupname
                    tmp.save()
                    groupname = new_groupname
                persetlist = request.POST.getlist('per_set')
                usersetlist = request.POST.getlist('user_set')
                pri.del_ugroup(groupname)
                s_perlist, s_userlist = pri.create_ugroup(groupname, persetlist,usersetlist)
                return render(request, 'previliges/u_group.html', locals())
            except Exception,e:
                info = "SET FAILED!"
                return render(request, 'previliges/u_group.html', locals())
    else:
        pri.init_ugroup()
        return render(request, 'previliges/u_group.html', locals())



def acc_list_callback(request):

    selected_host = json.loads(request.GET.get('selected_values'))
    text = request.GET.get('text')
    for host in selected_host:
        text = text.replace('value="{}"'.format(host),'selected value="{}"'.format(host))
    return HttpResponse(json.dumps(text))




@login_required(login_url='/accounts/login/')
@permission_verify()
def add_db(request):
    if request.method == 'GET':
        try:
            db = {}
            py = prpcrypt()
            instance_id = request.GET['instance_id']
            db_accounts = Db_account.objects.filter(instance_id=instance_id)
            db_instance = Db_instance.objects.get(id=instance_id)

            for db_account in db_accounts:
                db_names = Db_name.objects.filter(dbaccount_id=db_account.id)
                ip = db_instance.ip
                port = db_instance.port
                db_account_role = db_account.db_account_role
                db_account_user = db_account.user
                db_account_password = db_account.passwd
                sql = '''select schema_name from information_schema.SCHEMATA where schema_name not in ('mysql','information_schema','test'); '''

                data,result = func_mysql_query(sql,user=db_account_user,passwd=py.decrypt(db_account_password),
                                 host=ip, port=int(port), dbname=None, limitnum=100)
                if result[0] == 'error':
                    info = ''
                    db[db_account_role] = {}
                    for i in db_names:
                        db[db_account_role][i.dbname] =  -1
                    # return JsonResponse(db)

                else:
                    db[db_account_role] ={}
                    for i in data:
                        # 0:real db exists,local not exists 1:local exists 2:local exists ,but real server not exists this db
                        #-1:can not connect remote server ,status is uvaliable
                        db[db_account_role][i[0]] = 1 if i[0] in [dbname.dbname for dbname in db_names] else 0
                    for dbname in db_names:
                       if (dbname.dbname,) not in data:
                           db[db_account_role][dbname.dbname] = 2

            return JsonResponse(db)

        except Exception,e:
            print e
    elif request.method == 'POST':
        try:
            data = json.loads(request.POST['data'])
            db_account_roles = filter(lambda role:len(data[role])>0 ,data)
            save_flag = request.POST['save_flag']

            instance_id = request.POST['instance_id']
            for role in data:
                if Db_account.objects.filter(instance_id=instance_id,db_account_role=role).exists():
                    db_account = Db_account.objects.get(instance_id=instance_id,db_account_role=role)
                    if int(save_flag) == -1:
                        dbs = Db_name.objects.filter(dbaccount_id=db_account.id).exclude(dbname__in=(tuple([db.split(':')[0] for db in data[role]])))
                        dbs.delete()
                    if len(data[role]) > 0:
                        for db in data[role]:
                            dbtag = db.split(':')[1] if len(db.split(':')) >1 else ''
                            dbname = db.split(':')[0]

                            if Db_name.objects.filter(dbname=dbname, dbaccount_id=db_account.id).exists():
                                database_in_local = Db_name.objects.get(dbname=dbname, dbaccount_id=db_account.id)
                                database_in_local.update_date = timezone.now()
                                database_in_local.update_user = request.user.username
                                database_in_local.save()
                            else:
                                Db_name.objects.create(dbtag=dbtag, dbname=dbname, create_user=request.user.username, dbaccount_id=db_account.id)

                    else:
                        continue
                else:
                    continue
            return HttpResponse('success')
        except Exception,e:
            return HttpResponse(e)

class CheckBoxException(Exception):
    pass

@login_required(login_url='/accounts/login/')
@permission_verify()
def add_sys_account_perm(request):
    if request.method == 'GET':
        try:
            db_list = []
            sys_account = UserInfo.objects.get(username=request.GET['sys_account'])
            instance_id = request.GET['instance_id']

            dbs = Db_instance.objects.filter(id=instance_id,db_account__db_name__id__isnull=False).values('db_account__db_name__id', 'ip', 'port',
                                                                    'db_account__db_name__dbname', 'db_account__db_account_role',
                                                                    'db_account__db_name__dbtag')

            for db in dbs:
                temp_list = {}

                temp_list['ip'] = db['ip']
                temp_list['db_account_role'] = db['db_account__db_account_role']
                temp_list['port'] = db['port']
                temp_list['dbname'] = db['db_account__db_name__dbname']
                temp_list['dbname_id'] = db['db_account__db_name__id']
                temp_list['dbtag'] = db['db_account__db_name__dbtag']
                sys_account_has_perm = Db_database_permission.objects.filter(account_id=sys_account.id,db_name_id=db['db_account__db_name__id'])
                temp_list['db_database_permission_id'] = sys_account_has_perm[0].id if len(sys_account_has_perm)>0 else 0
                temp_list['sys_account_perm'] = sys_account_has_perm[0].permission if len(sys_account_has_perm)>0 else 'no'
                db_list.append(temp_list)
            # print db_list
            admin = Db_instance.objects.filter(id=instance_id,admin_user = sys_account)
            is_admin = True if len(admin) > 0 else False
            return JsonResponse({'db_list':db_list,'is_admin':is_admin},safe=False)
        except Exception,e:
            print e
            return HttpResponse(e)

    elif request.method == 'POST':
        try:

            sys_accounts = json.loads(request.POST['sys_accounts'])
            dbs = json.loads(request.POST['data'])
            save_flag = request.POST['save_flag']
            is_admin = request.POST['is_admin']
            instance = Db_instance.objects.get(id=int(request.POST['instance_id']))
            if len(sys_accounts) == 0:
                raise Exception

            for sys_account in sys_accounts:
                account = UserInfo.objects.get(username=sys_account)
                if int(save_flag) == -1:
                    #: empty exists db permission
                    exists_db_permission = Db_database_permission.objects.filter(
                        db_name__dbaccount__instance=instance.id, account=account.id)
                    exists_db_permission.delete()
                    instance.admin_user.remove(account)
                if int(is_admin) == 1:
                    instance.admin_user.add(account)
                else:
                    instance.admin_user.remove(account)
                if len(dbs) ==0 and int(save_flag) <> -1:
                    raise CheckBoxException('没有选择任何行，请选择红色提交，将会清空该实例下所有数据库权限')
                else:
                    for db in dbs:
                        permission = ''
                        if db['read'] is True:
                            permission = 'read'
                        if db['write'] is True:
                            permission = 'write'
                        if db['read_write'] is True:
                            permission = 'read_write'
                        if db['all'] is True:
                            permission = 'all'
                        dbname_id = db['dbname_id']


                        if Db_database_permission.objects.filter(db_name_id=dbname_id,account_id=account.id).exists():
                            per = Db_database_permission.objects.get(db_name_id=dbname_id,account_id=account.id)
                            per.permission = permission
                            per.update_user = request.user.username
                            per.save()
                        else:
                            Db_database_permission.objects.create(db_name_id=dbname_id, account_id=account.id,create_user=request.user.username,permission=permission)

            return HttpResponse('success')

        except Exception,e:
            return HttpResponse(e)
            print e



@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def get_user_permission(request):

    select_host = request.GET.get('select_host')
    user = request.GET.get('userid')
    userinfo = UserInfo.objects.get(username=user)
    account_id = userinfo.id
    data = list(Db_database_permission.objects.filter(account__id=account_id).values('id',
                                                                                      'permission',
                                                                                      'db_name_id',
                                                                                      'db_name__dbname',
                                                                                      'db_name__dbaccount__instance__ip',
                                                                                      'db_name__dbaccount__instance__port',
                                                                                      'db_name__dbaccount__db_account_role'
                                                                                  ))

    return HttpResponse(json.dumps({'data':data}))

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def perm_detail_edit(request,db_database_permission_id):
    perm_list = ['insert','update','delete','create','alter','rename','drop','truncate','replace']
    db_database_permission_id = db_database_permission_id
    sys_account_perm = Db_database_permission.objects.get(id=db_database_permission_id)
    if request.method == 'GET':
        if Db_database_permission_detail.objects.filter(permission__id=db_database_permission_id).exists():
            permission_detail = Db_database_permission_detail.objects.get(permission__id=db_database_permission_id)
            permission_has = json.loads(permission_detail.permission_detail)
            black_table_has = json.loads(permission_detail.black_table)
        else:
            if sys_account_perm.permission == 'read':
                permission_has = [-1]
            else:
                permission_has = [1]
            black_table_has = []

        return render(request, 'perm_detail_edit.html', locals())


    elif request.method == 'POST':
        try:
            status = '1'
            if sys_account_perm.permission == 'read':
                permission_list = json.dumps([-1])
            else:
                permission_list = request.POST.getlist('check_box_list')
                permission_list.insert(0,1)
                permission_list = json.dumps(permission_list)
            black_table = request.POST.get("table_name") if len(request.POST.get("table_name")) > 0 else  json.dumps([])


            if Db_database_permission_detail.objects.filter(permission__id=db_database_permission_id).exists():

                permission_detail = Db_database_permission_detail.objects.get(permission__id=db_database_permission_id)
                permission_detail.permission_detail=permission_list
                permission_detail.black_table=black_table
                permission_detail.update_user=request.user.username
                permission_detail.save()
            else:
                Db_database_permission_detail.objects.create(permission_id=db_database_permission_id,permission_detail=permission_list,
                                                     black_table=black_table,create_user=request.user.username)


            return render(request, 'perm_detail_edit.html', locals())
        except Exception,e:
            status = '2'
            return render(request, 'perm_detail_edit.html', locals())




@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def set_dbname(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    dblist,inslist,userlist = pri.get_fulldbname()
    acc_userlist = UserInfo.objects.all().order_by('username')
    acclist = Db_account.objects.all().order_by('tags')
    public_user = func.public_user
    host_group = HostGroup.objects.filter(name__istartswith='db')
    form = AddDBAccountSetDB()
    token = func.generate_token(request.user.username)

    text = request.POST.get('text')
    hostlist = request.POST.getlist('accdb_set')

    if text is not None and hostlist is not None:
        text = text.replace('selected=""', '')
        for host in hostlist:
            text = text.replace('value="{}"'.format(host), 'selected value="{}"'.format(host))

    if request.method == 'POST':

        session_token = request.session.get('postToken', default=None)
        token = request.POST['authenticity_token']
        if session_token == token:
            select_group = int(request.POST['select_group']) if request.POST.has_key('select_group') else 0


            if request.POST.has_key('ins_set') and len(request.POST['ins_set'].split('.')) == 1 :
                select_host = Db_instance.objects.get(id=request.POST['ins_set'])
            elif request.POST.has_key('ins_set') and len(request.POST['ins_set'].split('.')) == 4:
                select_host = Host.objects.get(ip=request.POST['ins_set'])
            else:
                select_host = 0
            if request.POST.has_key('query'):
                try:
                    dbtagname = request.POST['dbtag_set']
                    dbtagdt = pri.get_dbtag_detail(dbtagname)
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    return render(request, 'previliges/set_dbname.html', locals())
            elif request.POST.has_key('delete'):
                try:
                    dbtagname = request.POST['dbtag_set']
                    info = "DELETE OK!"
                    pri.del_dbtag(dbtagname)
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "DELETE FAILED!"
                    return render(request, 'previliges/set_dbname.html', locals())
            elif request.POST.has_key('create'):
                try:
                    info = "CREATE OK!"
                    dbtagname = request.POST['newdbtag']
                    newdbname = request.POST['newdbname']
                    inssetlist = request.POST.getlist('dbname_set')
                    usersetlist = request.POST.getlist('user_set')
                    dbtagdt = pri.create_dbtag(dbtagname,newdbname,inssetlist,usersetlist)
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "CREATE FAILED!"
                    return render(request, 'previliges/set_dbname.html', locals())
            elif request.POST.has_key('set'):
                try:
                    info = "SET OK!"
                    dbtagname = request.POST['dbtag_set']
                    inssetlist = request.POST.getlist('dbname_set')
                    usersetlist = request.POST.getlist('user_set')

                    new_dbtagname = request.POST['newdbtag']
                    newdbname = request.POST['newdbname']
                    dbtagdt = pri.set_dbtag(dbtagname,new_dbtagname,newdbname,inssetlist, usersetlist)
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    # print dbtagdt
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "SET FAILED!"
                    return render(request, 'previliges/set_dbname.html', locals())


            elif request.POST.has_key('query_ins'):
                try:

                    insnames  = HostGroup.objects.filter(id = select_group).values('host__ip')
                    host_list = {}
                    for ip in insnames if select_host == 0 else [{'host__ip':select_host.ip}]:
                        host = ip['host__ip']
                        db_accounts = Db_instance.objects.filter(ip=host).values('id','port','db_account__user','db_account__db_account_role','db_account__id').order_by('port','db_account__db_account_role')
                        p = {}
                        if db_accounts:
                            for port in db_accounts:
                                if p.has_key(port['port']):
                                    p[port['port']].append([port['db_account__user'],port['db_account__db_account_role']])
                                else:
                                    p[port['port']] = []
                                    p[port['port']].append([port['db_account__user'], port['db_account__db_account_role']])

                            host_list[host] = p
                        else:
                            host_list[host] = {'':[[None,None]]}
                    print host_list

                    return render(request, 'previliges/set_dbname.html', locals())

                except Exception,e:
                    return render(request, 'previliges/set_dbname.html', locals())

            elif request.POST.has_key('set_ins'):
                try:
                    info = "SET OK!"
                    insname  = Db_instance.objects.get(id = int(request.POST['ins_set']))

                    # newinsname = Db_instance.objects.get(id = int(request.POST['newinsport']))
                    if not Host.objects.filter(ip=request.POST['newinsip']):
                        raise Exception


                    insname = pri.set_ins(insname,request.POST['newinsip'],request.POST['newinsport'],request.POST['role'],request.POST['dbtype'],request.POST['comments'],request.user.username)
                    select_host = Db_instance.objects.get(id=request.POST['ins_set'])
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "SET FAILED!NewIP may be not exists,"
                    return render(request, 'previliges/set_dbname.html', locals())

            elif request.POST.has_key('create_ins'):
                try:
                    info = "CREATE OK!"

                    insname = pri.create_dbinstance(setip=request.POST['newinsip'],setport=request.POST['newinsport'],
                                                    status=request.POST['role'],setdbtype=request.POST['dbtype'],comments=request.POST['comments'],
                                                    create_user=request.user)
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "CREATE FAILED!"
                    return render(request, 'previliges/set_dbname.html', locals())
            elif request.POST.has_key('delete_ins'):
                try:
                    insname  = Db_instance.objects.get(id = int(request.POST['ins_set']))

                    info = "DELETE OK!"
                    insname.delete()
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "删除失败，可能此服务器不存在任何实例,"
                    return render(request, 'previliges/set_dbname.html', locals())
            # elif request.POST.has_key('query_acc'):
            #     try:
            #         account_set = Db_account.objects.get(id = int(request.POST['acc_set']))
            #         return render(request, 'previliges/set_dbname.html', locals())
            #     except Exception,e:
            #         return render(request, 'previliges/set_dbname.html', locals())
            elif request.POST.has_key('create_acc'):

                form = AddDBAccountSetDB(request.POST)
                if form.is_valid():
                    try:
                        info = "CREATE db_account OK!"

                        if len(hostlist) == 0:
                            error = ' At least one instance should be choice '
                            raise Exception

                        acc_role = request.POST['acc_role']

                        for host in hostlist:
                            ip = host.split(':')[0]
                            port = host.split(':')[1]
                            if len(port) > 0:
                                instance = Db_instance.objects.get(ip=ip,port=port)

                                db_account = Db_account.objects.filter(instance=instance,db_account_role=acc_role)
                                if len(db_account) >0:
                                    continue
                                else:
                                    data = form.cleaned_data
                                    new_account = data.get('normal_db_account')
                                    new_passwd = data.get('normal_db_password')
                                    create_user = request.user.username
                                    py = prpcrypt()
                                    account_set = Db_account.objects.create(user=new_account,
                                                                            passwd=py.encrypt(new_passwd),
                                                                            db_account_role=acc_role,
                                                                            create_user=create_user,
                                                                            instance=instance,
                                                                            tags='{instance_id}_{role}'.format(instance_id=instance.id,role=acc_role))
                        create_accout_text =text
                        del request.session['postToken']
                        token = func.generate_token(request.user.username)
                        request.session['postToken'] = token
                        form = AddDBAccountSetDB()
                        return render(request, 'previliges/set_dbname.html', locals())
                    except Exception,e:
                        create_accout_text = text
                        info = "CREATE db_account FAILED!"
                        return render(request, 'previliges/set_dbname.html', locals())
                else:
                    create_accout_text = text
                    errors = form.errors
                    print text

                    return render(request, 'previliges/set_dbname.html', locals())

            elif request.POST.has_key('clear_account'):
                account_list  = request.POST.getlist('accdb_set')
                try:
                    for instance in account_list:
                        ip = instance.split(':')[0]
                        port = instance.split(':')[1]
                        if len(port) > 0:

                                db_account = Db_account.objects.filter(instance__ip=ip, instance__port=port)
                                db_account.delete()
                    result = 'clear success'
                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())

                    # return redirect(reverse('set_dbname',kwargs={'query_ins':u'','select_group':select_group}))
                except Exception,e:
                    result = e
                    return render(request, 'previliges/set_dbname.html', locals())


            elif request.POST.has_key('set_acc'):
                try:
                    update_user = request.user.username
                    info = "SET db_account OK!"
                    author_list = request.POST.getlist('accdb_set')
                    if len(author_list) > 1:
                        raise Exception
                    # dbtagname = request.POST['dbtag_set']
                    old_account = Db_account.objects.get(id = author_list[0])
                    if len(request.POST['normal_db_account']) == 0:
                        db_account_role = request.POST.get('acc_role')
                        old_account.db_account_role=db_account_role
                        old_account.update_user=update_user
                        old_account.save()
                    else:
                        form = AddDBAccountSetDB(request.POST)
                        if form.is_valid():
                            py = prpcrypt()
                            data = form.cleaned_data
                            normal_db_account = data.get('normal_db_account')
                            normal_db_password= py.encrypt(data.get('normal_db_account'))
                            db_account_role = request.POST['acc_role']
                            old_account.user=normal_db_account
                            old_account.upasswd=normal_db_password
                            old_account.udb_account_role=db_account_role
                            old_account.utags=old_account.tags.replace(old_account.db_account_role,db_account_role)
                            old_account.uupdate_user=update_user
                            old_account.save()
                        else:
                            raise Exception


                    del request.session['postToken']
                    token = func.generate_token(request.user.username)
                    request.session['postToken'] = token
                    return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "SET db_account FAILED!"
                    return render(request, 'previliges/set_dbname.html', locals())

            elif request.POST.has_key('delete_acc'):
                try:
                    account_list = request.POST.getlist('accdb_set')


                    account_set = Db_account.objects.filter(id__in=tuple(account_list))

                    if len(set([i['mysql_monitor__id'] for i in Db_account.objects.filter(id__in=tuple(account_list)).values('mysql_monitor__id')])) != 1:
                        info = "DELETE db_account FAILED!ACCOUNT USED FOR MONITOR"
                        return render(request, 'previliges/set_dbname.html', locals())
                    else:
                        info = "DELETE db_account OK!"

                        result = 'clear success'
                        account_set.delete()
                        del request.session['postToken']
                        token = func.generate_token(request.user.username)
                        request.session['postToken'] = token
                        return render(request, 'previliges/set_dbname.html', locals())
                except Exception,e:
                    info = "DELETE db_account FAILED!"
                    return render(request, 'previliges/set_dbname.html', locals())
            elif request.POST.has_key('encrypt'):
                pri.encrypt_passwd()
                return render(request, 'previliges/set_dbname.html', locals())
        else:
            return redirect(reverse('set_dbname'))

    else:
        pri.check_pubuser()
        request.session['postToken'] = token
        return render(request, 'previliges/set_dbname.html', locals())




def get_hostdetail(request):
    host = request.GET.get('selected_host')
    if len(host.split('.')) == 1:
        try:

            host_detail = Db_instance.objects.get(id=int(host))
            result = 1
            return HttpResponse(json.dumps({'result': result,'comments': host_detail.comments,
                                            'port':host_detail.port,'db_type':host_detail.db_type,
                                            'status':host_detail.status
                                            })
                                )
        except Exception,e:
            result = e
            return HttpResponse(json.dumps({'result':e}))
    elif len(host.split('.')) == 4:
        return HttpResponse(json.dumps({'result': '''Doesn't have any instance,create it first!'''}))
    else:
        return HttpResponse(json.dumps({'result': '''Please contact SA '''}))




@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def get_host(request):
    group_id = request.GET.get('host_group')
    host_list = func_get_host(group_id)
    print(host_list)
    return HttpResponse(json.dumps({'host_list':host_list}))



def func_get_host(group_id):
    host = Host.objects.filter(group__id=int(group_id)).order_by('ip')
    host_list = {}
    for h in host:
        host_ip = h.ip
        host_name = h.hostname
        host_list[host_ip] = []
        try:

            db_instance = Db_instance.objects.filter(ip=host_ip)
            port_account_role = db_instance.all().values('port', 'id','db_account__user','db_account__db_account_role')
            for p in port_account_role:
                host_list[host_ip].append((p['id'],p['port'], p['db_account__user'], p['db_account__db_account_role']))



        except Exception, e:
            print e
    h = {}
    not_v_flag = -1
    for k, v in host_list.items():


        if len(v) > 0:
            for port_account in v:

                if h.has_key(port_account[0]):
                    h[port_account[0]][k + ':' + port_account[1]].append([port_account[2], port_account[3]])
                else:
                    h[port_account[0]] = {}
                    h[port_account[0]][k + ':' + port_account[1]] = []
                    h[port_account[0]][k + ':' + port_account[1]].append([port_account[2], port_account[3]])
        else:
            h[not_v_flag]={k:[[None, None]]}
            not_v_flag -= 1
    return h




@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_set_pri', login_url='/')
@permission_verify()
def fast_dbset(request):

    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    token = func.generate_token(request.user.username)

    if request.method == 'GET':
        form = AddDBAccount()
        request.session['postToken'] = token
        return render(request, 'previliges/fast_dbset.html',{'form': form, 'temp_name': temp_name, 'host_group': host_group,'token':token})
        # return render(request,'register.html',{'form':obj})
    elif request.method == 'POST':
            # print(request.POST)
            session_token = request.session.get('postToken',default=None)
            db_type = request.POST.get('db_type')
            token = request.POST['authenticity_token']
            if session_token == token:


                form = AddDBAccount(request.POST)
                select_group = int(request.POST.get('select_group')) if request.POST.get('select_group') is not None else 0


                if request.POST.has_key('select_host') and len(request.POST['select_host'].split('.')) == 1:
                    select_host = Db_instance.objects.get(id=request.POST['select_host'])
                elif request.POST.has_key('select_host') and len(request.POST['select_host'].split('.')) == 4:
                    select_host = Host.objects.get(ip=request.POST['select_host'])
                else:
                    select_host = 0

                if select_group is not None and select_host is not None and db_type is not None:

                    if form.is_valid() :
                        data = form.cleaned_data
                        # print(data)
                        port = data.get('port')
                        create_user = request.user
                        db_type = request.POST.get('db_type')
                        comment = request.POST.get('comment')
                        normal_db_account = data.get('normal_db_account')
                        normal_db_password = data.get('normal_db_password')
                        admin_db_account = data.get('admin_db_account')
                        admin_db_password = data.get('admin_db_password')

                        # )
                        # models.User.objects.create(username=username, nickname=nickname, password=password, email=email)
                        try:
                            Db_instance.objects.create(ip=select_host.ip,port=port,create_user=create_user,status='InUse',db_type=db_type,
                                                       comments=comment)
                        except Exception,e:
                            print e
                        py = prpcrypt()
                        instance = Db_instance.objects.get(ip=select_host.ip,port=port)
                        try:
                            if len(normal_db_account)>0 :
                                Db_account.objects.create(user=normal_db_account,passwd=py.encrypt(normal_db_password),
                                                          db_account_role='read_write',create_user=create_user,instance=instance,
                                                          tags='{instance_id}_{role}'.format(instance_id=instance.id,port=port,role='read_write'))

                            if len(admin_db_account)>0:
                                Db_account.objects.create(user=admin_db_account, passwd=py.encrypt(admin_db_password),
                                                          db_account_role='admin', create_user=create_user, instance=instance,
                                                          tags='{instance_id}_{role}'.format(instance_id=instance.id, port=port,
                                                                                           role='admin'))
                            result = '成功创建OK!!'
                            del request.session['postToken']
                            form = AddDBAccount()
                            token = func.generate_token(request.user.username)
                            request.session['postToken'] = token
                            return render(request, 'previliges/fast_dbset.html',{'form': form, 'temp_name': temp_name, 'host_group': host_group,
                                           'result': result,'token':token}
                                          )
                        except Exception,e:
                            print e
                        return render(request, 'previliges/fast_dbset.html',
                                      {'form': form, 'temp_name': temp_name, 'host_group': host_group,'db_type':db_type,
                                       'result': e})

                    else:
                        errors = form.errors
                        print('hello')
                        return render(request, 'previliges/fast_dbset.html',{'form': form, 'temp_name': temp_name, 'host_group': host_group,'select_host':select_host,'select_group':int(select_group),'token':token,'db_type':db_type,})
                else:
                    message = '服务器组、实例 DB TYPE必须选择,'
                    return render(request, 'previliges/fast_dbset.html',{'form': form, 'temp_name': temp_name, 'host_group': host_group,'message':message,'select_host':select_host,'select_group':int(select_group),'token':token,'db_type':db_type,})




            else:
                return redirect(reverse('fast_dbset'))




#table structure
# @login_required(login_url='/accounts/login/')
# @permission_required('dbmanage.myapp.can_see_metadata', login_url='/')



@login_required(login_url='/accounts/login/')
@permission_verify()
def meta_data(request):

    try:
        favword = request.COOKIES['myfavword']
    except Exception,e:
        pass
    # objlist = func.get_mysql_hostlist(request.user.username, 'meta')
    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    if request.method == 'POST':
        try:
            db_name = request.POST['optionsRadios'].split(':')[1]
            db_account = Db_account.objects.get(id=int(request.POST['optionsRadios'].split(':')[0]))

            # table_se = request.POST['searchname']
            if request.POST.has_key('query'):
                (data_list, collist, dbname) = meta.get_metadata(db_name,db_account,1)
                return render(request, 'meta_data.html', locals())
            elif request.POST.has_key('structure'):
                tbname = request.POST['structure'].split(';')[0]
                (field, col, dbname) = meta.get_metadata(db_name,db_account,2,tbname)
                (ind_data, ind_col, dbname) = meta.get_metadata(db_name,db_account, 3, tbname)
                (tbst, tbst_col, dbname) = meta.get_metadata(db_name,db_account, 4, tbname)
                (sh_cre, sh_cre_col, dbname) = meta.get_metadata(db_name,db_account, 5, tbname)

                return render(request, 'meta_data.html', locals())
            # elif request.POST.has_key('search'):
            #     print table_se
            #     (data_list, collist, dbname) = meta.get_metadata(db_name,db_account, 1,table_se)
            #     return render(request, 'meta_data.html', locals())
        except Exception,e:
            return render(request, 'meta_data.html', locals())
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='query')
        return JsonResponse(db_list, safe=False)
    elif request.GET.has_key('instance_id'):
        return HttpResponse(json.dumps(func.get_hostlist(request, tag='query')))
    else:
        return render(request, 'meta_data.html', locals())


@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def mysql_admin(request):

    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    if request.method == 'POST':
        try:
            # selfsql = request.POST['selfsql'].strip()
            insname = Db_instance.objects.get(id=int(request.POST['instance_id']))
            # tmpli = []
            # for i in insname.db_name_set.all():
            #     for x in i.instance.all():
            #         tmpli.append(int(x.id))
            # tmpli = list(set(tmpli))
            # bro = Db_instance.objects.filter(id__in=tmpli)
            tbody = get_template('admin/fullpro.html')
            if request.POST['event'] == 'fullpro':
                event = 'fullpro'
                data_list, col_list = meta.process(insname,1)
                col_list = [{'title':t} for t in col_list]
                data_list = [list(i) for i in data_list]
                if len(col_list) > 1 and col_list[0]['title'] <> 'error':
                    col_list.append({'title':"<input  id='id_all_all' onclick='all_check("+'"'+'id_all_all'+'"'+")' type='checkbox'>All"})
                    data_list = [list(i) for i in data_list]
                    [i.append('<input id="id_checkbox_'+str(i[0])+'_all" name="all_all_box" '+'type="checkbox">')  for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list':data_list,
                                                'col_list':col_list,'success': True}))

            elif  request.POST['event'] == 'showactive':
                event = 'showactive'
                data_list, col_list = meta.process(insname,2)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                if len(col_list) > 1 and col_list[0]['title'] <> 'error':
                    col_list.append({'title': "<input  id='id_all_all' onclick='all_check(" + '"' + 'id_all_all' + '"' + ")' type='checkbox'>All"})
                    data_list = [list(i) for i in data_list]
                    [i.append('<input id="id_checkbox_' + str(i[0]) + '_all" name="all_all_box" ' + 'type="checkbox">') for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))

            elif request.POST['event'] == 'showengine':
                data_list, col_list = meta.process(insname, 3)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list[0][2] = data_list[0][2].replace('\n','<br>')
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
            elif request.POST['event'] == 'kill_list':
                idlist = json.loads(request.POST['kill_list'])
                event = 'kill_list'
                data_list, col_list = meta.run_process(request,insname,idlist)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': [['success']], 'col_list': col_list, 'success': True}))

            elif request.POST['event']  == 'showmutex':
                data_list, col_list = meta.process(insname, 5)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
            elif request.POST['event']  == 'showbigtb':
                data_list, col_list = meta.process(insname, 6)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))

            elif request.POST['event'] == 'showstatus':
                vir = request.POST['variables'].strip()
                sql = "show global status like '%" + vir +"%'"
                data_list, col_list = meta.process(insname, 7,sql)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
            elif request.POST['event'] == 'showinc':
                data_list, col_list = meta.process(insname, 8)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))

            elif request.POST['event'] == 'showvari':
                vir = request.POST['variables'].strip()
                sql = "show global variables like '%" + vir + "%'"
                data_list, col_list = meta.process(insname, 7,sql)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
                return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))

            elif request.POST['event'] == 'slavestatus':
                sql = "show slave status"
                data_list, col_list = meta.process(insname, 7,sql)
                col_list = [{'title': t} for t in col_list]
                data_list = [list(i) for i in data_list]
                # data_list = [list(i) for i in zip([t['title'] for t in col_list],list(data_list[0]))]
                # col_list = [{'title':'NAME'},{'title':'VALUE'},{'title':'NAME'},{'title':'VALUE'},{'title':'NAME'},{'title':'VALUE'},{'title':'NAME'},{'title':'VALUE'}] if len(col_list) > 1 and col_list[0]['title'] <> 'error' else col_list
                final_list = []
                # while len(data_list) > 0:
                #     if len(data_list) > 3:
                #         final_list.append(data_list[0] + data_list[1] + data_list[2] + data_list[3])
                #         del data_list[0:3]
                #     else:
                #         final_list.append(data_list[0] + data_list[1] + data_list[2] + ['',''])
                #         del data_list[0:]
                # print final_list
                data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else final_list
                return HttpResponse(json.dumps({'data_list': data_list if len(final_list)<10 else final_list, 'col_list': col_list, 'success': True}))
            # elif request.POST['event'] == 'search':
            #     vir = request.POST['variables'].strip()
            #     a = Db_instance.objects.filter(ip__icontains=vir)
            #     bro =''
            #     if a:
            #         inslist = a
            #     else:
            #         info = "IP NOT FOUND"
            #     data_list, col_list = meta.process(insname, 7, sql)
            #     col_list = [{'title': t} for t in col_list]
            #     data_list = [list(i) for i in data_list]
            #     return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
            # elif request.POST['event'] == 'execute':
            #     bro = ''
            #     data_list, col_list = meta.process(insname, 7, meta.check_selfsql(selfsql))
            #     col_list = [{'title': t} for t in col_list]
            #     data_list = [list(i) for i in data_list]
            #     return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
        except Exception,e:

            return HttpResponse(e)
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='admin')
        return JsonResponse(db_list, safe=False)

    else:
        return render(request, 'admin/mysql_admin.html', locals())

def format_datalist(col_list,data_list):
    data_list = [list(i) for i in data_list]
    data_list = [[str(i) if isinstance(i, Decimal) else i for i in d] for d in data_list]
    data_list = [[i.strftime('%Y-%m-%d %H:%M:%S') if isinstance(i, datetime) else i for i in d] for d in
                 data_list]
    data_list.pop() if len(col_list) == 1 and col_list[0]['title'] == 'error' else data_list
    return data_list
@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def tb_check(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)

    # objlist = func.get_mysql_hostlist(request.user.username, 'meta')
    if request.method == 'POST':
        # choosed_host = request.POST['choosed']
        instance = Db_instance.objects.filter(id=int(request.POST['instance_id']))
        group =  int(request.POST['group_id'])
        if request.POST['event'] == 'bigtb':
            data_list,col_list = meta.get_his_meta(group if group <> 0 else 'all',instance[0].id if len(instance)>0 else 'all',1)
            col_list = [{'title': t} for t in col_list]
            data_list = format_datalist(col_list,data_list)
            return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
        elif request.POST['event'] == 'auto_occ':
            data_list, col_list = meta.get_his_meta(group if group <> 0 else 'all',instance[0].id if len(instance)>0 else 'all',2)
            col_list = [{'title': t} for t in col_list]
            data_list = format_datalist(col_list, data_list)
            return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
        elif request.POST['event'] == 'tb_incre':
            data_list, col_list = meta.get_his_meta(group if group <> 0 else 'all',instance[0].id if len(instance)>0 else 'all',3)
            col_list = [{'title': t} for t in col_list]
            data_list = format_datalist(col_list, data_list)
            return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
        elif request.POST['event'] == 'db_sz':
            data_list, col_list = meta.get_his_meta(group if group <> 0 else 'all',instance[0].id if len(instance)>0 else 'all', 4)
            col_list = [{'title': t} for t in col_list]
            data_list = format_datalist(col_list, data_list)
            return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
        elif request.POST['event'] == 'db_inc':
            data_list, col_list = meta.get_his_meta(group if group <> 0 else 'all',instance[0].id if len(instance)>0 else 'all', 5)
            col_list = [{'title': t} for t in col_list]
            data_list = format_datalist(col_list, data_list)
            return HttpResponse(json.dumps({'data_list': data_list, 'col_list': col_list, 'success': True}))
        # return render(request, 'admin/tb_check.html', locals())
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='admin')
        return JsonResponse(db_list, safe=False)


    else:
        return render(request, 'admin/tb_check.html', locals())

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def dupkey_check(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    # ins_li=get_dupreport_all()
    # print ins_li
    # objlist = func.get_mysql_hostlist(request.user.username, 'meta')
    if request.method == 'POST':

        if not request.POST.has_key('ins_set'):
            info = "Please choice host"

        else:
            choosed_host = request.POST['ins_set']
            tar_dbname = request.POST['optionsRadios']
            if request.POST.has_key('dupkey'):
                dupkey_result = get_dupreport(choosed_host,tar_dbname)
            elif request.POST.has_key('dupkey_mail'):
                get_dupreport.delay(choosed_host,tar_dbname,request.user.email)
                info = "mail send,check your email later"
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='admin')
        return JsonResponse(db_list, safe=False)
    return render(request, 'admin/dupkey_check.html', locals())



@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def mysql_binlog_parse(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    host_group = HostGroup.objects.filter(name__istartswith='db')
    select_group = request.POST.get('select_group') if request.POST.get('select_group') is not None else 0
    select_host = request.POST.get('ins_set') if request.POST.get('ins_set') is not None else 0
    select_group = int(select_group)
    select_host = int(select_host)
    if request.method == 'POST':
        try:
            binlist = []
            dblist = []
            serverid = int(request.POST['ins_set'])
            insname = Db_instance.objects.get(id=serverid)
            datalist, col_binary = meta.get_process_data(insname, 'show binary logs')
            dbresult, col_database = meta.get_process_data(insname, 'show databases')
            if col_binary != ['error'] and col_database != ['error']:
                for i in datalist:
                    binlist.append(i[0].ljust(20,' ')+str(i[1]))
                for i in dbresult:
                    dblist.append(i[0])
            else:
                del binlist
                info = col_binary + datalist[0]
                return render(request, 'admin/binlog_parse.html', locals())
            if request.POST.has_key('show_binary'):
                return render(request, 'admin/binlog_parse.html', locals())
            elif request.POST.has_key('parse'):
                binname = request.POST['binary_list'].split(' ')[0]
                countnum = int(request.POST['countnum'])
                if countnum not in [10,50,200]:
                    countnum = 10
                # print countnum
                begintime = request.POST['begin_time']
                tbname = request.POST['tbname']
                dbselected = request.POST['dblist']
                # parse_binlog.delay(serverid, binname, begintime, tbname, dbselected, request.user.username, countnum,False)
                parse_binlog(serverid, binname, begintime, tbname, dbselected,request.user.username,countnum,False)
                info = "Binlog REDO Parse mission uploaded"
            elif request.POST.has_key('parse_first'):
                binname = request.POST['binary_list'].split(' ')[0]
                sqllist = parse_binlogfirst(insname, binname, 5)
            elif request.POST.has_key('parse_undo'):
                binname = request.POST['binary_list'].split(' ')[0]
                countnum = int(request.POST['countnum'])
                if countnum not in [10, 50, 200]:
                    countnum = 10
                begintime = request.POST['begin_time']
                tbname = request.POST['tbname']
                dbselected = request.POST['dblist']
                # parse_binlog.delay(insname, binname, begintime, tbname, dbselected, request.user.username, countnum,True)
                parse_binlog(insname, binname, begintime, tbname, dbselected, request.user.username, countnum,True)
                info = "Binlog UNDO Parse mission uploaded"
        except Exception,e:
            pass
        return render(request, 'admin/binlog_parse.html', locals())
    elif request.GET.has_key('host_group'):
        db_list = func.get_hostlist(request, tag='admin')
        return JsonResponse(db_list, safe=False)
    else:
        return render(request, 'admin/binlog_parse.html', locals())

@login_required(login_url='/accounts/login/')
def pass_reset(request):
    if request.method == 'POST':
        try:
        # newpasswd = request.POST['passwd'].strip()
            tmp = UserInfo.objects.get(username=request.user.username)
            tmp.set_password(request.POST['passwd'].strip())
            tmp.save()
            info = "reset passwd ok"
            return render(request, 'previliges/pass_reset.html', locals())
        except:
            info = "reset passwd failed"
            return render(request, 'previliges/pass_reset.html', locals())
    else:
        return render(request, 'previliges/pass_reset.html', locals())


@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_metadata', login_url='/')
@permission_verify()
def get_tblist(request):
    choosed_host = request.GET['dbtag'].split(';')[0]
    if len(choosed_host) >0 and choosed_host in func.get_mysql_hostlist(request.user.username, 'meta'):
        tblist = map(lambda x:x[0],meta.get_metadata(choosed_host, 6))
    else :
        tblist = ['wrong dbname',]
    return HttpResponse(json.dumps(tblist), content_type='application/json')

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_metadata', login_url='/')
@permission_verify()
def diff(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    objlist = func.get_mysql_hostlist(request.user.username, 'meta')
    # result = func.get_diff('mysql-lepus-test','mysql_replication','mysql-lepus','mysql_replication')
    # print result
    if request.method == 'POST':
        if  request.POST.has_key('check'):
            choosed_host1 = request.POST['choosedb1'].split(';')[0]
            choosed_host2 = request.POST['choosedb2'].split(';')[0]
            choosed_tb1 = request.POST['choosetb1'].split(';')[0]
            choosed_tb2 = request.POST['choosetb2'].split(';')[0]
            if choosed_host1 in objlist and choosed_host2 in objlist:
                result = func.get_diff(choosed_host1, choosed_tb1, choosed_host2, choosed_tb2)
                (sh_cre1, sh_cre_col, dbname) = meta.get_metadata(choosed_host1, 5, choosed_tb1)
                (sh_cre2, sh_cre_col, dbname) = meta.get_metadata(choosed_host2, 5, choosed_tb2)
    return render(request,'diff.html', locals())



def get_db(request):
    instance = Db_instance.objects.get(id=int(request.GET['instance_id']))
    data_list, col_list = meta.process(instance, 9)
    if len(col_list) > 1 and col_list[0] <> 'error':
        result = [dict(zip(col_list, i)) for i in data_list]
        return HttpResponse(json.dumps({'result':result,'success':True}))
    else:
        return HttpResponse(json.dumps({'result':data_list[0][0],'success':False}))





# @ratelimit(key=func.my_key, rate='5/h')
# def test(request):
#     try:
#         xaxis = []
#         yaxis = []
#         choosed_host = request.GET['dbtag']
#         days_before = int(request.GET['day'])
#         if days_before not in [7,15,30]:
#             days_before = 7
#         if choosed_host!='all':
#             data_list, col = meta.get_hist_dbinfo(choosed_host,days_before)
#         elif choosed_host == 'all':
#             return JsonResponse({'xaxis': ['not support all'], 'yaxis': [1]})
#         for i in data_list:
#             xaxis.append(i[0])
#             yaxis.append(i[1])
#         mydata = {'xaxis':xaxis,'yaxis':yaxis}
#     except Exception,e:
#         print e
#         mydata = {'xaxis': ['error'], 'yaxis': [1]}
#     return JsonResponse(mydata)
#

# def tb_inc_status(request):
#     xaxis7 = []
#     yaxis7 = []
#     xaxis15 = []
#     yaxis15 = []
#     xaxis30 = []
#     yaxis30 = []
#     choosed_host = request.GET['dbtag']
#     tbname = request.GET['tbname'].strip()
#     print choosed_host
#     print tbname
#     print len(tbname)
#     data_list7, col7 = meta.get_hist_tbinfo(choosed_host,tbname,7)
#     data_list15,col15 = meta.get_hist_tbinfo(choosed_host,tbname,15)
#     data_list30, col30 = meta.get_hist_tbinfo(choosed_host, tbname, 30)
#     for i in data_list7:
#         xaxis7.append(i[0])
#         yaxis7.append(i[1])
#     for i in data_list15:
#         xaxis15.append(i[0])
#         yaxis15.append(i[1])
#     for i in data_list30:
#         xaxis30.append(i[0])
#         yaxis30.append(i[1])
#     return JsonResponse({'xaxis7': xaxis7, 'yaxis7': yaxis7,'xaxis15': xaxis15, 'yaxis15': yaxis15,'xaxis30': xaxis30, 'yaxis30': yaxis30})