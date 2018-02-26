from __future__ import unicode_literals
# from django.contrib.auth.models import User
from django.db import models
import pytz
from django.conf import settings
from datetime import datetime
from django.utils import timezone
tz = pytz.timezone('UTC')
s_time = tz.localize(datetime.strptime('2199-01-01 00:00:00','%Y-%m-%d %H:%M:%S'))
read_write = (
    ('read', 'read'),
    ('write', 'write'),
    ('all','all'),
    ('idle','idle'),
)
read_write_account = (
    ('read', 'read'),
    ('write', 'write'),
    ('read_write','read_write'),
    ('admin','admin'),
    ('all','all'),
)
db_type = (
    ('mysql', 'mysql'),
    ('mongodb', 'write'),
)


class Db_instance(models.Model):
    ip = models.CharField(max_length=30)
    port = models.CharField(max_length=10)
    db_type = models.CharField(max_length=30,default='mysql')
    comments = models.CharField(max_length=100,null=True)
    status = models.CharField(max_length=20,choices=(('Idle','Idle'),('InUse','InUse')))

    admin_user = models.ManyToManyField(settings.AUTH_USER_MODEL)
    create_user = models.CharField(max_length=50,null=True)
    create_date =models.DateTimeField(auto_now_add=timezone.now())
    update_user = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(auto_now=timezone.now())
    def __unicode__(self):
        return u'%s %s %s' % (self.ip, self.port,self.db_type)
    class Meta:
        unique_together = ("ip","port")



class Db_account(models.Model):

    user = models.CharField(max_length=30)
    passwd = models.CharField(max_length=255)
    instance = models.ForeignKey(Db_instance)
    db_account_role =  models.CharField(max_length=30,choices=read_write_account,default='all')
    tags = models.CharField(max_length=80,db_index=True)
    create_user = models.CharField(max_length=50, null=True)
    create_date = models.DateTimeField(auto_now_add=timezone.now())
    update_user = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(auto_now=timezone.now())
    # dbname = models.ManyToManyField(Db_name)
    # account = models.ManyToManyField(settings.AUTH_USER_MODEL)
    def __unicode__(self):
        return  u'%s %s' % ( self.tags,self.db_account_role)

    class Meta:
        unique_together = ('instance','db_account_role')

class Db_name (models.Model):
    dbtag = models.CharField(max_length=80)
    dbname = models.CharField(max_length=30)
    dbaccount = models.ForeignKey(Db_account)
    create_user = models.CharField(max_length=50, null=True)
    create_date = models.DateTimeField(auto_now_add=timezone.now())
    update_user = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(auto_now=timezone.now())
    def __unicode__(self):
        return u'%s %s' % (self.dbtag, self.dbname)

class Instance_account_admin(models.Model):
    account = models.ForeignKey(settings.AUTH_USER_MODEL)
    db_account = models.ForeignKey(Db_account)
class Db_database_permission(models.Model):
    db_name = models.ForeignKey(Db_name)
    account = models.ForeignKey(settings.AUTH_USER_MODEL)
    permission = models.CharField(max_length=20,choices=read_write_account,default='read')
    create_user = models.CharField(max_length=50, null=True)
    create_date = models.DateTimeField(auto_now_add=timezone.now())
    update_user = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(auto_now=timezone.now())

class Db_database_permission_detail(models.Model):
    permission = models.ForeignKey(Db_database_permission)
    permission_detail = models.CharField(max_length=500,null=True)
    black_table = models.CharField(max_length=500,null=True)
    create_user = models.CharField(max_length=50, null=True)
    create_date = models.DateTimeField(auto_now_add=timezone.now())
    update_user = models.CharField(max_length=50, null=True)
    update_date = models.DateTimeField(auto_now=timezone.now())

class Db_group(models.Model):
    groupname = models.CharField(max_length=30,unique=True)
    dbname = models.ManyToManyField(Db_name)
    account = models.ManyToManyField(settings.AUTH_USER_MODEL)
    def __unicode__(self):
        return self.groupname

class Oper_log(models.Model):
    user = models.CharField(max_length=35)
    ipaddr = models.CharField(max_length=35)
    dbtag = models.CharField(max_length=35)
    dbname = models.CharField(max_length=300)
    sqltext = models.TextField()
    sqltype = models.CharField(max_length=20)
    create_time = models.DateTimeField(db_index=True)
    login_time = models.DateTimeField()
    group_id = models.IntegerField()
    host_id = models.IntegerField()
    def __unicode__(self):
        return self.dbtag
    class Meta:
        index_together = [["dbtag","sqltype", "create_time"],]

class Login_log(models.Model):
    user = models.CharField(max_length=35)
    ipaddr = models.CharField(max_length=35)
    action = models.CharField(max_length=20)
    create_time = models.DateTimeField(db_index=True)

# class Task_scheduler(models.Model):
#     task = models.OneToOneField(Task)
#     appoint_time = models.DateTimeField(db_index=True)
#     def __unicode__(self):
#         return  self.task.id


class User_profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    select_limit = models.IntegerField(default=200)
    export_limit = models.IntegerField(default=200)
    task_email = models.IntegerField(db_index=True)
    def __unicode__(self):
        return  self.user.username
    class Meta:
        permissions = (('can_mysql_query','can see mysql_query view'),
                      ('can_log_query','can see log_query view'),
                      ('can_see_execview','can see mysql exec view'),
                      ('can_see_inception', 'can see inception view'),
                      ('can_see_metadata', 'can see meta_data view'),
                      ('can_see_mysqladmin', 'can see mysql_admin view'),
                      ('can_export','can export csv'),
                      ('can_insert_mysql','can insert mysql'),
                      ('can_update_mysql','can update mysql'),
                      ('can_delete_mysql','can delete mysql'),
                      ('can_create_mysql','can create mysql'),
                      ('can_drop_mysql','can drop mysql'),
                      ('can_truncate_mysql','can truncate mysql'),
                      ('can_alter_mysql','can alter mysql'),
                      ('can_query_mongo', 'can query mongo'),
                      ('can_see_taskview', 'can see task view'),
                      ('can_admin_task','can admin task'),
                      ('can_delete_task', 'can delete task'),
                      ('can_update_task', 'can update task'),
                      ('can_query_pri', 'can query pri'),
                      ('can_set_pri', 'can set pri'),
                      ('can_oper_saltapi', 'can oper saltapi'),
                       )

class Upload(models.Model):
    username = models.CharField(max_length = 40)
    filename = models.FileField(upload_to = 'upload_sql')
    def __unicode__(self):
        return self.username
# Create your models here.
class Task(models.Model):
    user = models.CharField(max_length=35)
    instance = models.CharField(max_length=100)
    db_account_role = models.CharField(max_length=15)
    dbtag = models.CharField(max_length=35)
    sqltext = models.TextField()
    create_time = models.DateTimeField(db_index=True)
    update_time = models.DateTimeField()
    status = models.CharField(max_length=20,db_index=True)
    sqlsha =  models.TextField()
    sche_time = models.DateTimeField(db_index=True,null=True)
    specification = models.CharField(max_length=100,default='')
    operator = models.CharField(max_length=35, default='')
    backup_status = models.SmallIntegerField(default=1)
    def __unicode__(self):
        return self.dbtag
#backup_status
# o donot  backup
# 1 need  backup
# 2

class Incep_error_log(models.Model):
    task_id = models.IntegerField(null=True,default=0)
    myid = models.IntegerField()
    stage = models.CharField(max_length= 20)
    errlevel = models.IntegerField()
    stagestatus = models.CharField(max_length=40)
    errormessage = models.TextField()
    sqltext = models.TextField()
    affectrow = models.IntegerField()
    sequence = models.CharField(max_length=30,db_index=True)
    backup_db = models.CharField(max_length=100)
    execute_time = models.CharField(max_length=20)
    sqlsha = models.CharField(max_length=50)
    create_time = models.DateTimeField(db_index=True)
    finish_time = models.DateTimeField()

class MySQL_monitor(models.Model):
    tag = models.CharField(max_length=20)
    monitor = models.SmallIntegerField(default=1)
    instance = models.OneToOneField(Db_instance)
    # instance = models.ForeignKey(Db_instance)
    check_longsql = models.SmallIntegerField(default=0)
    longsql_time = models.SmallIntegerField(default=1200)
    longsql_autokill = models.SmallIntegerField(default=0)
    check_active = models.SmallIntegerField(default=0)
    active_threshold = models.SmallIntegerField(default=30)
    # account = models.OneToOneField(Db_account)
    table_check = models.SmallIntegerField(default=0)
    account = models.ForeignKey(Db_account)
    check_connections = models.SmallIntegerField(default=0)
    connection_threshold = models.IntegerField(default=1000)
    check_delay = models.SmallIntegerField(default=0)
    delay_threshold = models.IntegerField(default=3600)
    check_slave = models.SmallIntegerField(default=0)
    replchannel = models.CharField(max_length=30,default='0')
    alarm_times = models.SmallIntegerField(default=3)
    alarm_interval = models.SmallIntegerField(default=60)
    mail_to = models.CharField(max_length=255)
    def __unicode__(self):
        return self.tag
    class Meta:
        db_table = 'mysql_monitor'