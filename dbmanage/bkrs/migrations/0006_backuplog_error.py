# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-12 04:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bkrs', '0005_auto_20180211_1713'),
    ]

    operations = [
        migrations.AddField(
            model_name='backuplog',
            name='error',
            field=models.CharField(max_length=1000, null=True),
        ),
    ]
