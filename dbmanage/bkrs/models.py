# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils import timezone
from django.db import models
from dbmanage.myapp.models import Db_instance



class BackupServer(models.Model):
    name = models.CharField(max_length=50,db_index=True)
    type = models.CharField(max_length=50)
    ip = models.CharField(max_length=50)
    port = models.IntegerField()
    user = models.CharField(max_length=50)
    passwd = models.CharField(max_length=200)
    regdate = models.DateTimeField(auto_now_add=timezone.now())


    def __unicode__(self):
        return  '{name}_{type}'.format(name=self.name, type=self.type)


class BackupHostConf(models.Model):
    customers_name = models.CharField(max_length=50)
    customers_short = models.CharField(max_length=50)
    instance = models.ForeignKey(Db_instance,on_delete=models.SET_NULL,null=True)
    status = models.NullBooleanField(null=True)
    dbname = models.CharField(max_length=80,default='ALL')
    backup_server = models.ForeignKey(BackupServer)
    local_backup_dir = models.CharField(max_length=100)
    xtrabackup = models.NullBooleanField(null=True)
    xtrabackup_conf = models.CharField(max_length=200,null=True)
    xtrabackup_task = models.CharField(max_length=50,null=True)
    mysqldump = models.NullBooleanField(null=True)
    mysqldump_conf = models.CharField(max_length=200,null=True)
    mysqldump_task = models.CharField(max_length=50,null=True)
    binlog = models.NullBooleanField(null=True)
    binlog_conf = models.CharField(max_length=200,null=True)
    binlog_task = models.CharField(max_length=50,null=True)
    create_date = models.DateTimeField(auto_now_add=timezone.now())
    create_user = models.CharField(max_length=50)
    update_date = models.DateTimeField(auto_now=timezone.now(),null=True)
    update_user = models.CharField(max_length=50,null=True)
    def __unicode__(self):
        return '{ip}:{port}-{backup_server}'.format(ip =self.instance.ip,port=self.instance.port,backup_server=self.backup_server)

class BackupLog(models.Model):
    host = models.ForeignKey(Db_instance,on_delete=models.SET_NULL,null=True)
    hostname = models.CharField(max_length=50,null=True,db_index=True)
    ip = models.GenericIPAddressField(null=True)
    port = models.IntegerField(null=True)
    type = models.CharField(max_length=50,null=True)
    database = models.CharField(max_length=200,null=True)
    status = models.IntegerField(null=True)
    command =models.CharField(max_length=800,null=True)
    start_date = models.CharField(max_length=50,null=True)
    finish_date = models.CharField(max_length=50,null=True)
    master_log_file = models.CharField(max_length=50,null=True)
    master_log_pos = models.CharField(max_length=30,null=True)
    binlog_min_datetime = models.CharField(max_length=50,null=True)
    binlog_max_datetime = models.CharField(max_length=50, null=True)
    binlog_min_pos = models.CharField(max_length=50, null=True)
    binlog_max_pos = models.CharField(max_length=50, null=True)
    backup_local_path = models.CharField(max_length=200, null=True)
    backup_files = models.CharField(max_length=2000,null=True)
    backup_files_size = models.CharField(max_length=50,null=True)
    is_tar = models.BooleanField(default=False)
    local_tar_file = models.CharField(max_length=300)
    local_tar_file_md5 = models.CharField(max_length=200, null=True)
    remote_backup_host = models.ForeignKey(BackupServer,null=True)
    remote_backup_path = models.CharField(max_length=200,null=True)
    remote_tar_file = models.CharField(max_length=200,null=True)
    verify = models.BooleanField(default=False)
    verify_date = models.DateTimeField(null=True)
    error = models.CharField(max_length=1000,null=True)
    def __unicode__(self):
        return  '{hostname}_{ip}_{port}'.format(hostname=self.hostname,
                                                ip=self.ip  ,
                                                port=self.port )

class RestoreLog(models.Model):
    host = models.ForeignKey(Db_instance, on_delete=models.SET_NULL, null=True)
    hostname = models.CharField(max_length=50, null=True, db_index=True)
    ip = models.GenericIPAddressField(null=True)
    port = models.IntegerField(null=True)
    type = models.CharField(u'Restore type:FULL,INC,BINLOG,DUMP',max_length=50, null=True)
    restore_ip = models.GenericIPAddressField(u'resotre server ip', max_length=30)
    restore_file = models.CharField(u'restore files ', max_length=3000)
    restore_endpos = models.CharField(u'end of resotre datetime or binlog file pos', max_length=300)
    start_date = models.DateTimeField(u'start datetime', auto_created=True)
    end_date = models.DateTimeField(u'start datetime')
    spend_time = models.IntegerField(u'spend time mi')
    local_path = models.CharField(u'local path for backup saved', max_length=500)
    remote_path = models.CharField(u'remote path from  backup saved', max_length=500)
    remote_ip = models.GenericIPAddressField(u'remote storage server ip ', max_length=50)

    def __unicode__(self):
        return  '{hostname}_{ip}_{port}'.format(hostname=self.hostname,
                                                ip=self.ip ,
                                                port=self.port)



class backfailed(models.Model):
    # __tablename__ = 'backfailed'

    count_date = models.CharField(max_length=50,null=True)
    host = models.ForeignKey(Db_instance, on_delete=models.SET_NULL, null=True)
    ip = models.GenericIPAddressField(null=True)
    port = models.IntegerField(null=True)
    back_type = models.CharField(max_length=50,null=True)
    back_success = models.CharField(max_length=50,null=True)
    back_failed = models.CharField(max_length=50,null=True)
    error = models.CharField(max_length=1000,null=True)

    def __unicode__(self):
        return '<count_date %r>' % self.count_date

class count_day_status(models.Model):
    # __tablename__ = 'count_day_status'
    # id = db.Column(db.Integer, primary_key=True)
    count_date = models.CharField(max_length=50,null=True)
    back_file_success = models.BooleanField(default=False)
    back_customers_success = models.BooleanField(default=False)
    back_file_failed = models.BooleanField(default=False)
    back_customers_failed = models.BooleanField(default=False)

    def __repr__(self):
        return '<count_date %r>' % self.count_date

class count_mon_status(models.Model):
    # __tablename__ = 'count_mon_status'
    # id = db.Column(db.Integer, primary_key=True)
    count_date = models.DateTimeField(null=True)
    back_customers = models.BooleanField(default=False)
    back_customers_stop = models.BooleanField(default=False)
    back_file = models.BooleanField(default=False)

    def __repr__(self):
        return '<count_date %r>' % self.count_date
