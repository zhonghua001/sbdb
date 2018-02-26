# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import BackupHostConf,BackupLog
# Register your models here.
class AdminHost(admin.ModelAdmin):
    fields = ['hostname','ip','port','user','pwd']

class AdminBackupLog(admin.ModelAdmin):
    fields = ['host','backup_type','backup_start_date','backup_finish_date']


admin.site.register(BackupHostConf,AdminHost)
admin.site.register(BackupLog,AdminBackupLog)
