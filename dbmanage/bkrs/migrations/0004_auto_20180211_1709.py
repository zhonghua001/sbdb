# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-11 09:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bkrs', '0003_auto_20180211_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='backuplog',
            name='command',
            field=models.CharField(max_length=800, null=True),
        ),
        migrations.AddField(
            model_name='backuplog',
            name='database',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='backuplog',
            name='status',
            field=models.IntegerField(null=True),
        ),
    ]
