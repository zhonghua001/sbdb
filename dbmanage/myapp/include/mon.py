# -*- coding: utf-8 =*-
from celery import shared_task
import time,string
from django.template import loader
from dbmanage.myapp.models import MySQL_monitor
from dbmanage.myapp.models import Db_instance,Db_account
import MySQLdb,datetime
from dbmanage.myapp.include.encrypt import prpcrypt
from dbmanage.myapp.tasks import sendmail
from dbmanage.monitor.models import Mysql_processlist,Mysql_replication,MysqlStatus,Alarm,AlarmTemp
from dbmanage.myapp.include.scheduled import mysql_exec
from django.utils import timezone
from dbmanage.bkrs.models import BackupLog,count_day_status,count_mon_status,backfailed,BackupHostConf
import threading
import calendar

class Connect(object):
    def __init__(self,ip=None,port=None,user=None,passwd=None):
        self.ip = ip
        self.port = int(port)
        self.user = user
        self.passwd = passwd
    def query_mysql(self,sql):
        try:
            conn=MySQLdb.connect(host=self.ip,user=self.user,passwd=self.passwd,port=self.port,connect_timeout=5,charset='utf8')
            conn.select_db('information_schema')
            cursor = conn.cursor()
            count=cursor.execute(sql)
            index=cursor.description
            col=[]
            #get column name
            for i in index:
                col.append(i[0])
            result=cursor.fetchall()
            cursor.close()
            conn.close()
            return (result,col)
        except Exception,e:
            return([str(e)],''),['error']
    def kill_id(self,idlist):
        try:
            conn=MySQLdb.connect(host=self.ip,user=self.user,passwd=self.passwd,port=self.port,connect_timeout=5,charset='utf8')
            conn.select_db('information_schema')
            curs = conn.cursor()
            for i in idlist:
                try:
                    curs.execute(i)
                except Exception, e:
                    pass
            conn.commit()
            curs.close()
            conn.close()
            results = 'success'
        except Exception, e:
             results = 'error'
        return results

# active sql,long sql,slave stop,slave delay,connections
alarm_list = {
    1:'active sql',
    2:'long sql',
    3:'long sql killed',
    4:'slave stop',
    5:'slave delay',
    6:'connections',
    7:'server down'
}

# @task
# def sendmail_monitor(title,mailto,data,alarm_type):
#     if alarm_type in ['active sql','long sql'] and data!='ok':
#         mon_sqllist = data
#     elif data == 'ok':
#         alarm_information = alarm_type+'  ok'
#     else:
#         alarm_information = data
#         # print alarm_information
#     html_content = loader.render_to_string('include/mail_template.html', locals())
#     sendmail(title, mailto, html_content)



@shared_task()
def backup_statistics():
    try:
        #预设每个平台每天备份5个文件为成功
        everyday_back_file = 0

        #count_day_status
        back_file_success = 0
        back_customers_success = 0
        back_file_failed = 0
        back_customers_failed = 0

        #count_mon_status
        back_customers_mon = 0
        back_customers_stop_mon = 0
        back_file_cur_mon = 0

        def getMonthFirstDayAndLastDay(year=None, month=None):
            """
            :param year: 年份，默认是本年，可传int或str类型
            :param month: 月份，默认是本月，可传int或str类型
            :return: firstDay: 当月的第一天，datetime.date类型
                      lastDay: 当月的最后一天，datetime.date类型
            """
            if year:
                year = int(year)
            else:
                year = datetime.date.today().year

            if month:
                month = int(month)
            else:
                month = datetime.date.today().month

            # 获取当月第一天的星期和当月的总天数
            firstDayWeekDay, monthRange = calendar.monthrange(year, month)

            # 获取当月的第一天
            firstDay = datetime.date(year=year, month=month, day=1)
            lastDay = datetime.date(year=year, month=month, day=monthRange)

            return firstDay, lastDay

        firstday,lastday = getMonthFirstDayAndLastDay(datetime.datetime.today().year,datetime.datetime.today().month)
        cur_mon = str(time.strftime('%Y-%m',time.localtime(time.time())))
        yesterday = str(datetime.date.today()-datetime.timedelta(days=1))
        today = str(datetime.date.today()-datetime.timedelta(days=0))
        back_file_success = BackupLog.objects.filter(start_date__gte=yesterday,start_date__lte=today).count()
        back_file_failed = backfailed.objects.filter(start_date__gte=yesterday,start_date__lte=today).count()
        back_customers_failed = backfailed.objects.all().values('host').distinct().count()
        bback_customers_all= BackupLog.objects.all().values('host').distinct().count()
        back_customers_success = bback_customers_all - back_customers_failed
        count_day_status.objects.create(count_date=yesterday,
                                        back_file_success=back_file_success,
                                        back_customers_success=back_customers_success,
                                        back_file_failed=back_file_failed,
                                        back_customers_failed=back_customers_failed)

        back_customers_mon = BackupHostConf.objects.filter(status=0).count()
        back_customers_stop_mon = BackupHostConf.objects.filter(status=1).count()
        back_file_cur_mon = BackupLog.objects.filter(start_date__gte=firstday,start_date_lte=lastday)
        #     db.query("select count(*) from backarchives where DATE_FORMAT(back_time,'%%Y-%%m')='%s'" %cur_mon)[0][0]
        #
        # cur_mon_count = db.query("select id from count_mon_status where count_date='%s'" %cur_mon)
        # if cur_mon_count:
        #     cur_mon_id = cur_mon_count[0][0]
        #     sql = "update count_mon_status set back_customers=%s,back_customers_stop=%s,back_file=%s where id=%s" %(back_customers_mon,back_customers_stop_mon,back_file_cur_mon,cur_mon_id)
        #     #print sql
        #     db.update(sql)
        # else:
        #     sql = "insert into count_mon_status(count_date,back_customers,back_customers_stop,back_file) " \
        #           "values('%s',%s,%s,%s)" %(cur_mon,back_customers_mon,back_customers_stop_mon,back_file_cur_mon)
        #     #print sql
        #     db.update(sql)
        #
        # db.close()
    except:
        pass













@shared_task()
def sendmail_monitor(instance_id,mailto,data,alarm_type):
    instance = Db_instance.objects.get(id=instance_id)
    dbinfo  = 'IP: '+instance.ip + '\n' + 'PORT: ' + instance.port + '\n'
    title = ''
    if data=='ok':
        alarm_information = alarm_list[alarm_type] + '  ok'
        title = instance.ip+':'+instance.port+'['+instance.comments+']'+'---------'+alarm_information
    elif alarm_type in [1,2,3]:
        title = instance.ip+':'+instance.port+'['+instance.comments+']'+'---------'+ alarm_list[alarm_type]
        mon_sqllist = data
    elif alarm_type == 6:
        title = instance.ip+':'+instance.port+'['+instance.comments+']'+'---------'+ 'too many connections'
        alarm_information = 'values: '+ str(data)
    elif alarm_type == 5:
        title = instance.ip+':'+instance.port+'['+instance.comments+']'+'---------'+ alarm_list[alarm_type]
        alarm_information = 'values: '+ str(data)
    elif alarm_type == 4:
        alarm_information = 'SLAVE_IO_THREAD:'+ data['iothread'] + '\nSLAVE_SQL_THREAD:' + data['sqlthread'] + '\n'
        title = instance.ip+':'+instance.port+'['+instance.comments+']'+'---------'+ alarm_list[alarm_type]
    elif alarm_type == 7:
        title = instance.ip+':'+instance.port+'['+instance.comments+']'+'---------'+ alarm_list[alarm_type]
        alarm_information = "MySQL Server Down"
    html_content = loader.render_to_string('include/mail_template.html', locals())
    sendmail(title, mailto, html_content)

@shared_task()
def mon_mysql():
    monlist = MySQL_monitor.objects.filter(monitor=1)
    no_monlist = MySQL_monitor.objects.filter(monitor=0)
    if len(no_monlist)>0:
        for i in no_monlist:

            Mysql_replication.objects.filter(db_ip=i.instance.ip).filter(db_port=i.instance.port).delete()
            MysqlStatus.objects.filter(db_ip=i.instance.ip).filter(db_port=i.instance.port).delete()
    # plist=[]
    if len(monlist)>0:
        for i in monlist:

            # check_mysql.apply_async((i,),queue='mysql_monitor',routing_key='monitor.mysql')
            # check_mysql_host.delay(i.instance_id,i.account_id)
            t = threading.Thread(target=check_mysql_host,args=(i.instance_id,i.account_id,))
            t.start()
            print i.tag,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@shared_task()
def test(x,y):
    return x*y

@shared_task
def check_mysql_host(instance_id,account_id):
    instance = Db_instance.objects.get(id=instance_id)
    db_account = Db_account.objects.get(id=account_id)
    mon_basic(instance,db_account)
    # longlist = []
    py = prpcrypt()
    #
    conn_info  = Connect(instance.ip,instance.port,db_account.user,py.decrypt(db_account.passwd))
    result,col = conn_info.query_mysql("select ID,USER,HOST,DB,COMMAND,TIME,STATE,INFO from information_schema.processlist where COMMAND !='Sleep' and DB not in ('information_schema','sys') and user not in ('system user','event_scheduler') and command!='Binlog Dump' and info like 'select%'")
    # result,col = conn_info.query_mysql("select ID,USER,HOST,DB,COMMAND,TIME,STATE,INFO from processlist")
    mysql_monitor = MySQL_monitor.objects.get(instance_id=instance.id)
    if mysql_monitor.check_longsql == 1:
        try:
            longsql_send = filter(lambda x:int(x[5])>int(mysql_monitor.longsql_time),result)
        except Exception,e:
            longsql_send=''
        # print longsql_send
        alarm_type = 2
        if len(longsql_send)>0:
            flag = record_alarm(mysql_monitor, alarm_type)
            if mysql_monitor.longsql_autokill  == 1:
                idlist = map(lambda x:'kill '+str(x[0])+';',longsql_send)
                conn_info.kill_id(idlist)
                sendmail_monitor.delay(instance.id,mysql_monitor.mail_to.split(';'), longsql_send,3)
            elif flag:
                sendmail_monitor.delay(instance.id,mysql_monitor.mail_to.split(';'),longsql_send,alarm_type)
        else:
            check_ifok(instance, alarm_type)
    if mysql_monitor.check_active == 1 :
        alarm_type = 1
        if len(result)>=int(mysql_monitor.active_threshold) :
            if record_alarm(mysql_monitor, alarm_type):
                sendmail_monitor.delay(instance.id, mysql_monitor.mail_to.split(';'), result,alarm_type)
        else:
            check_ifok(instance, alarm_type)
    insertlist=[]
    # for i in result:
    #     insertlist.append(Mysql_processlist(conn_id=i[0],user=i[1],host=i[2],db=i[3],\
    #                                     command=i[4],time=i[5],state=i[6],info=i[7]))
    if len(result)>0 and  type(result[0][0]) == int :
        try:
            insertlist = map(lambda x:Mysql_processlist(db_ip=instance.ip,db_port=instance.port,
                                                        conn_id=x[0],user=x[1],host=x[2],db=x[3],
                                                        command=x[4],time=x[5],state=x[6],info=x[7]),result)
            # print insertlist
            Mysql_processlist.objects.bulk_create(insertlist)
        except Exception,e:
            print e



def record_alarm(mysql_monitor,num):
    instance = Db_instance.objects.get(id=mysql_monitor.instance_id)
    alarm_type = alarm_list[num]
    time = timezone.now()-datetime.timedelta(minutes=mysql_monitor.alarm_interval)

    if  len(AlarmTemp.objects.filter(db_ip=instance.ip, db_port=instance.port,alarm_type=alarm_type,create_time__gte=time))< int(mysql_monitor.alarm_times) + 2:

        new_alarm = Alarm(send_mail=1,db_ip=instance.ip, db_port=instance.port, alarm_type=alarm_type)
        new_alarm.save()
        new_alarm1 = AlarmTemp(db_ip=instance.ip, db_port=instance.port, alarm_type=alarm_type)
        new_alarm1.save()

        if len(AlarmTemp.objects.filter(db_ip=instance.ip, db_port=instance.port,alarm_type=alarm_type,create_time__gte=time)) <=2:
            new_alarm.send_mail = 0
            new_alarm.save()
            return False
        else:
            return True

    else:
        new_alarm = Alarm(send_mail=0, db_ip=instance.ip, db_port=instance.port, alarm_type=alarm_type)
        new_alarm.save()
        return False

def check_ifok(instance,num):

    alarm_type = alarm_list[num]
    mysql_monitor = MySQL_monitor.objects.get(instance_id=instance.id)
    if AlarmTemp.objects.filter(db_ip=instance.ip, db_port=instance.port,alarm_type=alarm_type)[:1]:
        AlarmTemp.objects.filter(db_ip=instance.ip, db_port=instance.port, alarm_type=alarm_type).delete()
        sendmail_monitor.delay(instance.id, mysql_monitor.mail_to.split(';'),'ok', num)



def mon_basic(instance,db_account):
    mysql_monitor = MySQL_monitor.objects.get(instance=instance.id)
    now_time = timezone.now()
    try:
        py = prpcrypt()
        conn = MySQLdb.connect(host=instance.ip, user=db_account.user, passwd=py.decrypt(db_account.passwd), port=int(instance.port), connect_timeout=3, charset='utf8')
        conn.autocommit(True)
        cur = conn.cursor()
        conn.select_db('information_schema')
        check_ifok(instance,7)
        ############################# CHECK MYSQL ####################################################
        mysql_variables = get_mysql_variables(cur)
        mysql_status = get_mysql_status(cur)
        time.sleep(1)
        mysql_status_2 = get_mysql_status(cur)
        ############################# GET VARIABLES ###################################################
        version = get_item(mysql_variables, 'version')
        key_buffer_size = get_item(mysql_variables, 'key_buffer_size')
        sort_buffer_size = get_item(mysql_variables, 'sort_buffer_size')
        join_buffer_size = get_item(mysql_variables, 'join_buffer_size')
        max_connections = get_item(mysql_variables, 'max_connections')
        max_connect_errors = get_item(mysql_variables, 'max_connect_errors')
        open_files_limit = get_item(mysql_variables, 'open_files_limit')
        table_open_cache = get_item(mysql_variables, 'table_open_cache')
        max_tmp_tables = get_item(mysql_variables, 'max_tmp_tables')
        max_heap_table_size = get_item(mysql_variables, 'max_heap_table_size')
        max_allowed_packet = get_item(mysql_variables, 'max_allowed_packet')
        thread_cache_size = get_item(mysql_variables, 'thread_cache_size')
        ############################# GET INNODB INFO ##################################################
        # innodb variables
        innodb_version = get_item(mysql_variables, 'innodb_version')
        innodb_buffer_pool_instances = get_item(mysql_variables, 'innodb_buffer_pool_instances')
        innodb_buffer_pool_size = get_item(mysql_variables, 'innodb_buffer_pool_size')
        innodb_doublewrite = get_item(mysql_variables, 'innodb_doublewrite')
        innodb_file_per_table = get_item(mysql_variables, 'innodb_file_per_table')
        innodb_flush_log_at_trx_commit = get_item(mysql_variables, 'innodb_flush_log_at_trx_commit')
        innodb_flush_method = get_item(mysql_variables, 'innodb_flush_method')
        innodb_force_recovery = get_item(mysql_variables, 'innodb_force_recovery')
        innodb_io_capacity = get_item(mysql_variables, 'innodb_io_capacity')
        innodb_read_io_threads = get_item(mysql_variables, 'innodb_read_io_threads')
        innodb_write_io_threads = get_item(mysql_variables, 'innodb_write_io_threads')
        # innodb status
        innodb_buffer_pool_pages_total = int(get_item(mysql_status, 'Innodb_buffer_pool_pages_total'))
        innodb_buffer_pool_pages_data = int(get_item(mysql_status, 'Innodb_buffer_pool_pages_data'))
        innodb_buffer_pool_pages_dirty = int(get_item(mysql_status, 'Innodb_buffer_pool_pages_dirty'))
        innodb_buffer_pool_pages_flushed = int(get_item(mysql_status, 'Innodb_buffer_pool_pages_flushed'))
        innodb_buffer_pool_pages_free = int(get_item(mysql_status, 'Innodb_buffer_pool_pages_free'))
        innodb_buffer_pool_pages_misc = int(get_item(mysql_status, 'Innodb_buffer_pool_pages_misc'))
        innodb_buffer_pool_wait_free = int(get_item(mysql_status, 'Innodb_buffer_pool_wait_free'))
        if innodb_buffer_pool_pages_misc > 18046744073709540000:
            innodb_buffer_pool_pages_misc = 0
        innodb_page_size = int(get_item(mysql_status, 'Innodb_page_size'))
        innodb_pages_created = int(get_item(mysql_status, 'Innodb_pages_created'))
        innodb_pages_read = int(get_item(mysql_status, 'Innodb_pages_read'))
        innodb_pages_written = int(get_item(mysql_status, 'Innodb_pages_written'))
        innodb_row_lock_current_waits = int(get_item(mysql_status, 'Innodb_row_lock_current_waits'))
        innodb_row_lock_time = int(get_item(mysql_status, 'Innodb_row_lock_time'))
        innodb_row_lock_waits = int(get_item(mysql_status, 'Innodb_row_lock_waits'))
        innodb_log_waits = int(get_item(mysql_status, 'Innodb_log_waits'))
        # innodb persecond info
        innodb_buffer_pool_read_requests_persecond = int(
            get_item(mysql_status_2, 'Innodb_buffer_pool_read_requests')) - int(
            get_item(mysql_status, 'Innodb_buffer_pool_read_requests'))
        innodb_buffer_pool_reads_persecond = int(get_item(mysql_status_2, 'Innodb_buffer_pool_reads')) - int(
            get_item(mysql_status, 'Innodb_buffer_pool_reads'))
        innodb_buffer_pool_write_requests_persecond = int(
            get_item(mysql_status_2, 'Innodb_buffer_pool_write_requests')) - int(
            get_item(mysql_status, 'Innodb_buffer_pool_write_requests'))
        innodb_buffer_pool_pages_flushed_persecond = int(
            get_item(mysql_status_2, 'Innodb_buffer_pool_pages_flushed')) - int(
            get_item(mysql_status, 'Innodb_buffer_pool_pages_flushed'))
        innodb_rows_deleted_persecond = int(get_item(mysql_status_2, 'Innodb_rows_deleted')) - int(
            get_item(mysql_status, 'Innodb_rows_deleted'))
        innodb_rows_inserted_persecond = int(get_item(mysql_status_2, 'Innodb_rows_inserted')) - int(
            get_item(mysql_status, 'Innodb_rows_inserted'))
        innodb_rows_read_persecond = int(get_item(mysql_status_2, 'Innodb_rows_read')) - int(
            get_item(mysql_status, 'Innodb_rows_read'))
        innodb_rows_updated_persecond = int(get_item(mysql_status_2, 'Innodb_rows_updated')) - int(
            get_item(mysql_status, 'Innodb_rows_updated'))
        ############################# GET STATUS ##################################################
        connect = 1
        uptime = get_item(mysql_status, 'Uptime')
        open_files = get_item(mysql_status, 'Open_files')
        open_tables = get_item(mysql_status, 'Open_tables')
        opened_tables = get_item(mysql_status, 'Opened_tables')
        threads_connected = get_item(mysql_status, 'Threads_connected')
        threads_running = get_item(mysql_status, 'Threads_running')
        threads_created = get_item(mysql_status, 'Threads_created')
        threads_cached = get_item(mysql_status, 'Threads_cached')
        # threads_waits = 20
        max_used_connections = get_item(mysql_status, 'Max_used_connections')
        connections = get_item(mysql_status, 'Connections')
        aborted_clients = get_item(mysql_status, 'Aborted_clients')
        aborted_connects = get_item(mysql_status, 'Aborted_connects')
        key_blocks_not_flushed = get_item(mysql_status, 'Key_blocks_not_flushed')
        key_blocks_unused = get_item(mysql_status, 'Key_blocks_unused')
        key_blocks_used = get_item(mysql_status, 'Key_blocks_used')
        slow_queries = int(get_item(mysql_status, 'Slow_queries'))
        ############################# GET STATUS PERSECOND ##################################################


        threads_created_percond = int(get_item(mysql_status_2, 'Threads_created')) - int(threads_created)
        connections_persecond = int(get_item(mysql_status_2, 'Connections')) - int(get_item(mysql_status, 'Connections'))
        bytes_received_persecond = (int(get_item(mysql_status_2, 'Bytes_received')) - int(
            get_item(mysql_status, 'Bytes_received'))) / 1024
        bytes_sent_persecond = (int(get_item(mysql_status_2, 'Bytes_sent')) - int(
            get_item(mysql_status, 'Bytes_sent'))) / 1024
        com_select_persecond = int(get_item(mysql_status_2, 'Com_select')) - int(get_item(mysql_status, 'Com_select'))
        com_insert_persecond = int(get_item(mysql_status_2, 'Com_insert')) - int(get_item(mysql_status, 'Com_insert'))
        com_update_persecond = int(get_item(mysql_status_2, 'Com_update')) - int(get_item(mysql_status, 'Com_update'))
        com_delete_persecond = int(get_item(mysql_status_2, 'Com_delete')) - int(get_item(mysql_status, 'Com_delete'))
        com_commit_persecond = int(get_item(mysql_status_2, 'Com_commit')) - int(get_item(mysql_status, 'Com_commit'))
        com_rollback_persecond = int(get_item(mysql_status_2, 'Com_rollback')) - int(get_item(mysql_status, 'Com_rollback'))
        questions_persecond = int(get_item(mysql_status_2, 'Questions')) - int(get_item(mysql_status, 'Questions'))
        queries_persecond = int(get_item(mysql_status_2, 'Queries')) - int(get_item(mysql_status, 'Queries'))
        transaction_persecond = (int(get_item(mysql_status_2, 'Com_commit')) + int(
            get_item(mysql_status_2, 'Com_rollback'))) - (
                                int(get_item(mysql_status, 'Com_commit')) + int(get_item(mysql_status, 'Com_rollback')))
        created_tmp_disk_tables_persecond = int(get_item(mysql_status_2, 'Created_tmp_disk_tables')) - int(
            get_item(mysql_status, 'Created_tmp_disk_tables'))
        created_tmp_files_persecond = int(get_item(mysql_status_2, 'Created_tmp_files')) - int(
            get_item(mysql_status, 'Created_tmp_files'))
        created_tmp_tables_persecond = int(get_item(mysql_status_2, 'Created_tmp_tables')) - int(
            get_item(mysql_status, 'Created_tmp_tables'))
        table_locks_immediate_persecond = int(get_item(mysql_status_2, 'Table_locks_immediate')) - int(
            get_item(mysql_status, 'Table_locks_immediate'))
        table_locks_waited_persecond = int(get_item(mysql_status_2, 'Table_locks_waited')) - int(
            get_item(mysql_status, 'Table_locks_waited'))
        key_read_requests_persecond = int(get_item(mysql_status_2, 'Key_read_requests')) - int(
            get_item(mysql_status, 'Key_read_requests'))
        key_reads_persecond = int(get_item(mysql_status_2, 'Key_reads')) - int(get_item(mysql_status, 'Key_reads'))
        key_write_requests_persecond = int(get_item(mysql_status_2, 'Key_write_requests')) - int(
            get_item(mysql_status, 'Key_write_requests'))
        key_writes_persecond = int(get_item(mysql_status_2, 'Key_writes')) - int(get_item(mysql_status, 'Key_writes'))
        ############################# GET MYSQL HITRATE ##################################################
        if (string.atof(get_item(mysql_status, 'Qcache_hits')) + string.atof(get_item(mysql_status, 'Com_select'))) <> 0:
            query_cache_hitrate = string.atof(get_item(mysql_status, 'Qcache_hits')) / (
            string.atof(get_item(mysql_status, 'Qcache_hits')) + string.atof(get_item(mysql_status, 'Com_select')))
            query_cache_hitrate = "%9.2f" % query_cache_hitrate
        else:
            query_cache_hitrate = 0

        if string.atof(get_item(mysql_status, 'Connections')) <> 0:
            thread_cache_hitrate = 1 - string.atof(get_item(mysql_status, 'Threads_created')) / string.atof(
                get_item(mysql_status, 'Connections'))
            thread_cache_hitrate = "%9.2f" % thread_cache_hitrate
        else:
            thread_cache_hitrate = 0

        if string.atof(get_item(mysql_status, 'Key_read_requests')) <> 0:
            key_buffer_read_rate = 1 - string.atof(get_item(mysql_status, 'Key_reads')) / string.atof(
                get_item(mysql_status, 'Key_read_requests'))
            key_buffer_read_rate = "%9.2f" % key_buffer_read_rate
        else:
            key_buffer_read_rate = 0

        if string.atof(get_item(mysql_status, 'Key_write_requests')) <> 0:
            key_buffer_write_rate = 1 - string.atof(get_item(mysql_status, 'Key_writes')) / string.atof(
                get_item(mysql_status, 'Key_write_requests'))
            key_buffer_write_rate = "%9.2f" % key_buffer_write_rate
        else:
            key_buffer_write_rate = 0

        if (string.atof(get_item(mysql_status, 'Key_blocks_used')) + string.atof(
                get_item(mysql_status, 'Key_blocks_unused'))) <> 0:
            key_blocks_used_rate = string.atof(get_item(mysql_status, 'Key_blocks_used')) / (
            string.atof(get_item(mysql_status, 'Key_blocks_used')) + string.atof(
                get_item(mysql_status, 'Key_blocks_unused')))
            key_blocks_used_rate = "%9.2f" % key_blocks_used_rate
        else:
            key_blocks_used_rate = 0

        if (string.atof(get_item(mysql_status, 'Created_tmp_disk_tables')) + string.atof(
                get_item(mysql_status, 'Created_tmp_tables'))) <> 0:
            created_tmp_disk_tables_rate = string.atof(get_item(mysql_status, 'Created_tmp_disk_tables')) / (
            string.atof(get_item(mysql_status, 'Created_tmp_disk_tables')) + string.atof(
                get_item(mysql_status, 'Created_tmp_tables')))
            created_tmp_disk_tables_rate = "%9.2f" % created_tmp_disk_tables_rate
        else:
            created_tmp_disk_tables_rate = 0

        if string.atof(max_connections) <> 0:
            connections_usage_rate = string.atof(threads_connected) / string.atof(max_connections)
            connections_usage_rate = "%9.2f" % connections_usage_rate
        else:
            connections_usage_rate = 0

        if string.atof(open_files_limit) <> 0:
            open_files_usage_rate = string.atof(open_files) / string.atof(open_files_limit)
            open_files_usage_rate = "%9.2f" % open_files_usage_rate
        else:
            open_files_usage_rate = 0

        if string.atof(table_open_cache) <> 0:
            open_tables_usage_rate = string.atof(open_tables) / string.atof(table_open_cache)
            open_tables_usage_rate = "%9.2f" % open_tables_usage_rate
        else:
            open_tables_usage_rate = 0

        # repl
        slave_status = cur.execute('show slave status;')
        if slave_status <> 0:
            role = 'slave'
            role_new = 's'
        else:
            role = 'master'
            role_new = 'm'
        ############################# INSERT INTO SERVER ##################################################
        sql_insert = "replace into mysql_status(db_ip,db_port,connect,role,uptime,version,max_connections,max_connect_errors,open_files_limit,table_open_cache,max_tmp_tables,max_heap_table_size,max_allowed_packet,open_files,open_tables,threads_connected,threads_running,threads_created,threads_cached,connections,aborted_clients,aborted_connects,connections_persecond,bytes_received_persecond,bytes_sent_persecond,com_select_persecond,com_insert_persecond,com_update_persecond,com_delete_persecond,com_commit_persecond,com_rollback_persecond,questions_persecond,queries_persecond,transaction_persecond,created_tmp_tables_persecond,created_tmp_disk_tables_persecond,created_tmp_files_persecond,table_locks_immediate_persecond,table_locks_waited_persecond,key_buffer_size,sort_buffer_size,join_buffer_size,key_blocks_not_flushed,key_blocks_unused,key_blocks_used,key_read_requests_persecond,key_reads_persecond,key_write_requests_persecond,key_writes_persecond,innodb_version,innodb_buffer_pool_instances,innodb_buffer_pool_size,innodb_doublewrite,innodb_file_per_table,innodb_flush_log_at_trx_commit,innodb_flush_method,innodb_force_recovery,innodb_io_capacity,innodb_read_io_threads,innodb_write_io_threads,innodb_buffer_pool_pages_total,innodb_buffer_pool_pages_data,innodb_buffer_pool_pages_dirty,innodb_buffer_pool_pages_flushed,innodb_buffer_pool_pages_free,innodb_buffer_pool_pages_misc,innodb_page_size,innodb_pages_created,innodb_pages_read,innodb_pages_written,innodb_row_lock_current_waits,innodb_buffer_pool_pages_flushed_persecond,innodb_buffer_pool_read_requests_persecond,innodb_buffer_pool_reads_persecond,innodb_buffer_pool_write_requests_persecond,innodb_rows_read_persecond,innodb_rows_inserted_persecond,innodb_rows_updated_persecond,innodb_rows_deleted_persecond,query_cache_hitrate,thread_cache_hitrate,key_buffer_read_rate,key_buffer_write_rate,key_blocks_used_rate,created_tmp_disk_tables_rate,connections_usage_rate,open_files_usage_rate,open_tables_usage_rate,create_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"

        sql_update = "update mysql_status set db_ip=%s,db_port=%s,connect=%s,role=%s,uptime=%s,version=%s,max_connections=%s,max_connect_errors=%s,open_files_limit=%s,table_open_cache=%s,max_tmp_tables=%s,max_heap_table_size=%s,max_allowed_packet=%s,open_files=%s,open_tables=%s,threads_connected=%s,threads_running=%s,threads_created=%s,threads_cached=%s,connections=%s,aborted_clients=%s,aborted_connects=%s,connections_persecond=%s,bytes_received_persecond=%s,bytes_sent_persecond=%s,com_select_persecond=%s,com_insert_persecond=%s,com_update_persecond=%s,com_delete_persecond=%s,com_commit_persecond=%s,com_rollback_persecond=%s,questions_persecond=%s,queries_persecond=%s,transaction_persecond=%s,created_tmp_tables_persecond=%s,created_tmp_disk_tables_persecond=%s,created_tmp_files_persecond=%s,table_locks_immediate_persecond=%s,table_locks_waited_persecond=%s,key_buffer_size=%s,sort_buffer_size=%s,join_buffer_size=%s,key_blocks_not_flushed=%s,key_blocks_unused=%s,key_blocks_used=%s,key_read_requests_persecond=%s,key_reads_persecond=%s,key_write_requests_persecond=%s,key_writes_persecond=%s,innodb_version=%s,innodb_buffer_pool_instances=%s,innodb_buffer_pool_size=%s,innodb_doublewrite=%s,innodb_file_per_table=%s,innodb_flush_log_at_trx_commit=%s,innodb_flush_method=%s,innodb_force_recovery=%s,innodb_io_capacity=%s,innodb_read_io_threads=%s,innodb_write_io_threads=%s,innodb_buffer_pool_pages_total=%s,innodb_buffer_pool_pages_data=%s,innodb_buffer_pool_pages_dirty=%s,innodb_buffer_pool_pages_flushed=%s,innodb_buffer_pool_pages_free=%s,innodb_buffer_pool_pages_misc=%s,innodb_page_size=%s,innodb_pages_created=%s,innodb_pages_read=%s,innodb_pages_written=%s,innodb_row_lock_current_waits=%s,innodb_buffer_pool_pages_flushed_persecond=%s,innodb_buffer_pool_read_requests_persecond=%s,innodb_buffer_pool_reads_persecond=%s,innodb_buffer_pool_write_requests_persecond=%s,innodb_rows_read_persecond=%s,innodb_rows_inserted_persecond=%s,innodb_rows_updated_persecond=%s,innodb_rows_deleted_persecond=%s,query_cache_hitrate=%s,thread_cache_hitrate=%s,key_buffer_read_rate=%s,key_buffer_write_rate=%s,key_blocks_used_rate=%s,created_tmp_disk_tables_rate=%s,connections_usage_rate=%s,open_files_usage_rate=%s,open_tables_usage_rate=%s,create_time=%s where db_ip=%s and db_port=%s; "
        sql2 = "insert into mysql_status_his(db_ip,db_port,connect,role,uptime,version,max_connections,max_connect_errors,open_files_limit,table_open_cache,max_tmp_tables,max_heap_table_size,max_allowed_packet,open_files,open_tables,threads_connected,threads_running,threads_created,threads_cached,connections,aborted_clients,aborted_connects,connections_persecond,bytes_received_persecond,bytes_sent_persecond,com_select_persecond,com_insert_persecond,com_update_persecond,com_delete_persecond,com_commit_persecond,com_rollback_persecond,questions_persecond,queries_persecond,transaction_persecond,created_tmp_tables_persecond,created_tmp_disk_tables_persecond,created_tmp_files_persecond,table_locks_immediate_persecond,table_locks_waited_persecond,key_buffer_size,sort_buffer_size,join_buffer_size,key_blocks_not_flushed,key_blocks_unused,key_blocks_used,key_read_requests_persecond,key_reads_persecond,key_write_requests_persecond,key_writes_persecond,innodb_version,innodb_buffer_pool_instances,innodb_buffer_pool_size,innodb_doublewrite,innodb_file_per_table,innodb_flush_log_at_trx_commit,innodb_flush_method,innodb_force_recovery,innodb_io_capacity,innodb_read_io_threads,innodb_write_io_threads,innodb_buffer_pool_pages_total,innodb_buffer_pool_pages_data,innodb_buffer_pool_pages_dirty,innodb_buffer_pool_pages_flushed,innodb_buffer_pool_pages_free,innodb_buffer_pool_pages_misc,innodb_page_size,innodb_pages_created,innodb_pages_read,innodb_pages_written,innodb_row_lock_current_waits,innodb_buffer_pool_pages_flushed_persecond,innodb_buffer_pool_read_requests_persecond,innodb_buffer_pool_reads_persecond,innodb_buffer_pool_write_requests_persecond,innodb_rows_read_persecond,innodb_rows_inserted_persecond,innodb_rows_updated_persecond,innodb_rows_deleted_persecond,query_cache_hitrate,thread_cache_hitrate,key_buffer_read_rate,key_buffer_write_rate,key_blocks_used_rate,created_tmp_disk_tables_rate,connections_usage_rate,open_files_usage_rate,open_tables_usage_rate,create_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        param = (
        instance.ip, int(instance.port), connect, role, uptime, version, max_connections, max_connect_errors, open_files_limit,
        table_open_cache, max_tmp_tables, max_heap_table_size, max_allowed_packet, open_files, open_tables,
        threads_connected, threads_running, threads_created, threads_cached, connections, aborted_clients,
        aborted_connects, connections_persecond, bytes_received_persecond, bytes_sent_persecond, com_select_persecond,
        com_insert_persecond, com_update_persecond, com_delete_persecond, com_commit_persecond, com_rollback_persecond,
        questions_persecond, queries_persecond, transaction_persecond, created_tmp_tables_persecond,
        created_tmp_disk_tables_persecond, created_tmp_files_persecond, table_locks_immediate_persecond,
        table_locks_waited_persecond, key_buffer_size, sort_buffer_size, join_buffer_size, key_blocks_not_flushed,
        key_blocks_unused, key_blocks_used, key_read_requests_persecond, key_reads_persecond, key_write_requests_persecond,
        key_writes_persecond, innodb_version, innodb_buffer_pool_instances, innodb_buffer_pool_size, innodb_doublewrite,
        innodb_file_per_table, innodb_flush_log_at_trx_commit, innodb_flush_method, innodb_force_recovery,
        innodb_io_capacity, innodb_read_io_threads, innodb_write_io_threads, innodb_buffer_pool_pages_total,
        innodb_buffer_pool_pages_data, innodb_buffer_pool_pages_dirty, innodb_buffer_pool_pages_flushed,
        innodb_buffer_pool_pages_free, innodb_buffer_pool_pages_misc, innodb_page_size, innodb_pages_created,
        innodb_pages_read, innodb_pages_written, innodb_row_lock_current_waits, innodb_buffer_pool_pages_flushed_persecond,
        innodb_buffer_pool_read_requests_persecond, innodb_buffer_pool_reads_persecond,
        innodb_buffer_pool_write_requests_persecond, innodb_rows_read_persecond, innodb_rows_inserted_persecond,
        innodb_rows_updated_persecond, innodb_rows_deleted_persecond, query_cache_hitrate, thread_cache_hitrate,
        key_buffer_read_rate, key_buffer_write_rate, key_blocks_used_rate, created_tmp_disk_tables_rate,
        connections_usage_rate, open_files_usage_rate, open_tables_usage_rate,now_time,instance.ip, int(instance.port))
        # print param
        if not MysqlStatus.objects.filter(db_ip=instance.ip,db_port=instance.port).exists():
            mysql_exec(sql_insert, param[:-2])
        else:
            mysql_exec(sql_update, param)

        mysql_exec(sql2,param[:-2])

        if mysql_monitor.check_connections:
            alarm_type = 6
            if mysql_monitor.connection_threshold <= int(threads_connected):
                if record_alarm(mysql_monitor,alarm_type):
                    sendmail_monitor.delay(instance.id, mysql_monitor.mail_to.split(';'),  threads_connected,alarm_type)
            else:
                check_ifok(instance, alarm_type)



        # check mysql connected
        connected = cur.execute("select SUBSTRING_INDEX(host,':',1) as connect_server, user connect_user,db connect_db, count(SUBSTRING_INDEX(host,':',1)) as connect_count  from information_schema.processlist where db is not null and db!='information_schema' and db !='performance_schema' group by connect_server,connect_user,connect_db;");
        if connected:
            for line in cur.fetchall():
                sql = "insert into mysql_connected(db_ip,db_port,connect_server,connect_user,connect_db,connect_count,create_time) values(%s,%s,%s,%s,%s,%s,%s);"
                param = (instance.ip, int(instance.port),line[0], line[1], line[2], line[3],now_time)
                mysql_exec(sql, param)

        #check replication
        master_thread=cur.execute("select * from information_schema.processlist where COMMAND = 'Binlog Dump' or COMMAND = 'Binlog Dump GTID';")
        slave_status=cur.execute('show slave status;')
        datalist=[]
        if master_thread >= 1:
            datalist.append(int(1))
            if slave_status <> 0:
                datalist.append(int(1))
            else:
                datalist.append(int(0))
        else:
            datalist.append(int(0))
            if slave_status <> 0:
                datalist.append(int(1))
            else:
                datalist.append(int(0))
                sql="delete from mysql_replication where db_ip=%s and db_port=%s;"
                param =(instance.ip,instance.port)
                mysql_exec(sql,param)
        if slave_status <> 0:
            gtid_mode=cur.execute("select * from information_schema.global_variables where variable_name='gtid_mode';")
            result=cur.fetchone()
            if result:
                gtid_mode=result[1]
            else:
                gtid_mode='OFF'
            datalist.append(gtid_mode)
            read_only=cur.execute("select * from information_schema.global_variables where variable_name='read_only';")
            result=cur.fetchone()
            datalist.append(result[1])
            #slave_info=cur.execute('show slave status;')
            if instance.replchannel <> '0':
                slave_info=cur.execute("show slave status for channel '%s';" %(instance.replchannel))
            else :
                slave_info=cur.execute('show slave status;')
            result=cur.fetchone()
            # print "result"
            # print slave_info
            master_server=result[1]
            master_port=result[3]
            slave_io_run=result[10]
            slave_sql_run=result[11]
            delay=result[32]
            current_binlog_file=result[9]
            current_binlog_pos=result[21]
            master_binlog_file=result[5]
            master_binlog_pos=result[6]
            try:
                slave_sQL_rnning_state=result[44]
            except Exception,e:
                slave_sQL_running_state="NULL"
            datalist.append(master_server)
            datalist.append(master_port)
            datalist.append(slave_io_run)
            datalist.append(slave_sql_run)
            datalist.append(delay)
            datalist.append(current_binlog_file)
            datalist.append(current_binlog_pos)
            datalist.append(master_binlog_file)
            datalist.append(master_binlog_pos)
            datalist.append(0)
            datalist.append(slave_sQL_rnning_state)

            if instance.check_slave:
                if (slave_io_run == "Yes") and (slave_sql_run == "Yes"):
                    alarm_type = 4
                    check_ifok(instance, alarm_type)
                    if instance.check_delay :
                        alarm_type = 5
                        if instance.delay_threshold <=int(delay) :
                            if record_alarm(instance,alarm_type):
                                sendmail_monitor.delay(instance.id, mysql_monitor.mail_to.split(';'),delay,alarm_type)

                        else:
                            check_ifok(instance, alarm_type)
                else:
                    alarm_type = 4
                    if record_alarm(instance,alarm_type):
                        sendmail_monitor.delay(instance.id, mysql_monitor.mail_to.split(';'),{'iothread':slave_io_run,'sqlthread':slave_sql_run}, alarm_type)




        elif master_thread >= 1:
            gtid_mode=cur.execute("select * from information_schema.global_variables where variable_name='gtid_mode';")
            result=cur.fetchone()
            if result:
                gtid_mode=result[1]
            else:
                gtid_mode='OFF'
            datalist.append(gtid_mode)
            read_only=cur.execute("select * from information_schema.global_variables where variable_name='read_only';")
            result=cur.fetchone()
            datalist.append(result[1])
            datalist.append('---')
            datalist.append('---')
            datalist.append('---')
            datalist.append('---')
            datalist.append('---')
            datalist.append('---')
            datalist.append('---')
            master=cur.execute('show master status;')
            master_result=cur.fetchone()
            datalist.append(master_result[0])
            datalist.append(master_result[1])
            binlog_file=cur.execute('show master logs;')
            binlogs=0
            if binlog_file:
                for row in cur.fetchall():
                    binlogs = binlogs + row[1]
                datalist.append(binlogs)
            datalist.append('---')
        else:
            datalist=[]
        result=datalist
        if result:
            datalist.append(now_time)
            sql= "update mysql_replication set db_ip=%s,db_port=%s,is_master=%s,is_slave=%s,gtid_mode=%s,read_only=%s,master_server=%s,master_port=%s,slave_io_run=%s,slave_sql_run=%s,delay=%s,current_binlog_file=%s,current_binlog_pos=%s,master_binlog_file=%s,master_binlog_pos=%s,master_binlog_space=%s,slave_sql_running_state=%s,create_time where db_ip=%s and db_port=%s"
            sql2= "insert into mysql_replication_his(db_ip,db_port,is_master,is_slave,gtid_mode,read_only,master_server,master_port,slave_io_run,slave_sql_run,delay,current_binlog_file,current_binlog_pos,master_binlog_file,master_binlog_pos,master_binlog_space,slave_sql_running_state,create_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            param=(instance.ip,instance.port,result[0],result[1],result[2],result[3],result[4],result[5],result[6],result[7],result[8],result[9],result[10],result[11],result[12],result[13],result[14],result[15],instance.ip,instance.port)
            mysql_exec(sql,param)
            mysql_exec(sql2, param[:-2])
        cur.close()
        conn.close()
    # except Exception, e:
    except MySQLdb.Error, e:
        print e
        time.sleep(3)
    try:
        conn = MySQLdb.connect(host=instance.ip, user=db_account.user, passwd=py.decrypt(db_account.passwd), port=int(instance.port), connect_timeout=3, charset='utf8')
        cur = conn.cursor()
        conn.select_db('information_schema')
    except MySQLdb.Error, e:
        connect = 0
        downserver = MysqlStatus.objects.filter(db_ip=instance.ip, db_port=int(instance.port))[:1]
        # now_time = now_time + datetime.timedelta(hours=8)
        if downserver:
            downserver[0].connect = 0
            downserver[0].create_time = now_time
            downserver[0].save()
        else:
            downserver = MysqlStatus(db_ip=instance.ip, db_port=int(instance.port),version='-1',create_time=now_time)
            downserver.save()
        alarm_type = 7
        if record_alarm(mysql_monitor, alarm_type):
            sendmail_monitor.delay(instance.id, mysql_monitor.mail_to.split(';'), alarm_type,alarm_type)
            # sendmail_monitor(instance.id, mysql_monitor.mail_to.split(';'), alarm_type, alarm_type)


def get_mysql_status(cursor):
    data=cursor.execute('show global status;');
    data_list=cursor.fetchall()
    data_dict={}
    for item in data_list:
        data_dict[item[0]] = item[1]
    return data_dict

def get_mysql_variables(cursor):
    cursor.execute('show global variables;')
    data_list=cursor.fetchall()
    data_dict={}
    for item in data_list:
        data_dict[item[0]] = item[1]
    return data_dict

def get_mysql_version(cursor):
    cursor.execute('select version();');
    return cursor.fetchone()[0]

def get_item(data_dict,item):
    try:
       item_value = data_dict[item]
       return item_value
    except:
       return '-1'