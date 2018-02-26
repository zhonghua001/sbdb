from django.shortcuts import render
from django.template.loader import get_template
from dbmanage.monitor.models import MysqlStatus,Mysql_replication
from dbmanage.myapp.models import Db_account,Db_instance,MySQL_monitor
from django.http import HttpResponse,HttpResponseRedirect,StreamingHttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required,permission_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.models import User
from accounts.permission import permission_verify
import json
from django.db.models import Q
# Create your views here.
@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def mon_set(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    page_size = 10
    all_record = MySQL_monitor.objects.all().order_by('id')
    paginator = Paginator(all_record, page_size)
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        posts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        posts = paginator.page(paginator.num_pages)

    return render(request,'mon_set.html',locals())






@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def mon_edit(request,mon_id):
    temp_name = 'dbmanage/dbmanage_header.html'

    ins_list = Db_instance.objects.filter(Q(mysql_monitor__instance__isnull=True) | Q(mysql_monitor__id=int(mon_id))).order_by('ip')


    if request.method == 'GET':
        if request.GET.has_key('db_instance_id'):
            instance_id = request.GET.get('db_instance_id')
            acc = Db_account.objects.filter(instance_id=instance_id)
            acc_list = []
            for a in acc:
                acc_list.append({'db_account_id':a.id,'db_account_user':a.user,'db_account_role':a.db_account_role})

            return HttpResponse(json.dumps(acc_list))

        try:
            myid = int(mon_id)

            edit_db = MySQL_monitor.objects.get(id=myid)
            acc_list = Db_account.objects.filter(instance=edit_db.instance_id)
        except :
            pass

    elif request.method == 'POST':
        try:
            status = '1'
            if request.POST.has_key('set'):
                myid = int(request.POST['set'])
                edit_db = MySQL_monitor.objects.get(id=myid)
                edit_db.tag = request.POST['tagset']
                edit_db.instance = Db_instance.objects.get(id=int(request.POST['ins_set']))
                edit_db.account = Db_account.objects.get(id=int(request.POST['acc_set']))
                edit_db.monitor = int(request.POST['monitor_set'])
                edit_db.check_longsql = int(request.POST['longsql_set'])
                edit_db.longsql_autokill = int(request.POST['autokill_set'])
                edit_db.longsql_time = int(request.POST['longthre_set'])
                edit_db.table_check = int(request.POST['table_check'])
                edit_db.check_active = int(request.POST['activesql_set'])
                edit_db.active_threshold = int(request.POST['activetre_set'])
                edit_db.replchannel = request.POST['slavechannel_set']
                edit_db.check_connections = int(request.POST['connection_set'])
                edit_db.connection_threshold = int(request.POST['connectiontre_set'])
                edit_db.check_slave =  int(request.POST['slave_set'])
                edit_db.check_delay = int(request.POST['slavedelay_set'])
                edit_db.delay_threshold = int(request.POST['slavedelaytre_set'])
                edit_db.alarm_times = int(request.POST['alarmtime_set'])
                edit_db.alarm_interval = int(request.POST['alarminterval_set'])
                edit_db.mail_to = request.POST['mailset']
                edit_db.save()
                acc_list = Db_account.objects.filter(instance=edit_db.instance_id)
            elif request.POST.has_key('delete'):
                myid = int(request.POST['set'])
                delete_mon(myid)
                return HttpResponseRedirect("/monitor/mon_set/")
            elif request.POST.has_key('create'):
                if request.POST['ins_set'] !='' and request.POST['acc_set']!='':
                    edit_db = MySQL_monitor(instance=Db_instance.objects.get(id=int(request.POST['ins_set'])),\
                                            account=Db_account.objects.get(id=int(request.POST['acc_set'])),\
                                            tag=request.POST['tagset'],monitor=int(request.POST['monitor_set']),table_check=int(request.POST['table_check']),\
                                            check_longsql=int(request.POST['longsql_set']),longsql_autokill=int(request.POST['autokill_set']),\
                                            longsql_time=int(request.POST['longthre_set']),check_active=int(request.POST['activesql_set']),\
                                            active_threshold=int(request.POST['activetre_set']),check_connections=int(request.POST['connection_set']), \
                                            connection_threshold=int(request.POST['connectiontre_set']),check_slave=int(request.POST['slave_set']), \
                                            check_delay=int(request.POST['slavedelay_set']),delay_threshold=int(request.POST['slavedelaytre_set']), \
                                            alarm_times=int(request.POST['alarmtime_set']),alarm_interval=int(request.POST['alarminterval_set']), \
                                            replchannel=request.POST['slavechannel_set'],mail_to=request.POST['mailset'])
                    edit_db.save()

        except Exception,e:
            status = '2'
            print e
            info = "set failed"
    return render(request,'mon_edit.html',locals())

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def mon_delete(request):

    myid = int(request.GET['dbid'])
    delete_mon(myid)
    return HttpResponseRedirect("/dbmanage/dbmonitor/mon_set/")

def delete_mon(id):
    db = MySQL_monitor.objects.get(id=id)
    MysqlStatus.objects.filter(db_ip=db.instance.ip,db_port=db.instance.port).delete()
    Mysql_replication.objects.filter(db_ip=db.instance.ip,db_port=db.instance.port).delete()
    MySQL_monitor.objects.get(id=id).delete()

@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def mysql_status(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    page_size = 15
    all_record = MysqlStatus.objects.order_by('db_ip')
    paginator = Paginator(all_record, page_size)
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        posts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        posts = paginator.page(paginator.num_pages)

    pager = get_template('mysql_status_pager.html')
    pager_html = pager.render(locals())


    tbody = get_template('mysql_status_tbody.html')
    tbody_html = tbody.render(locals())
    payload = {'tbody_html':tbody_html,'pager_html':pager_html,
               'success': True}
    return HttpResponse(json.dumps(payload))



@login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
@permission_verify()
def batch_add(request):
    temp_name = 'dbmanage/dbmanage_header.html'
    return render(request, 'batch_add.html', locals())


# @login_required(login_url='/accounts/login/')
# @permission_required('myapp.can_see_mysqladmin', login_url='/')
# def test_tb(request):
#     dbtag = request.GET['dbtag']
#     if dbtag!='all':
#         mydata = {'dupresult':get_dupreport(dbtag,request.GET['email'])}
#     # return render(request, 'batch_add.html', locals())
#     return JsonResponse(mydata)

