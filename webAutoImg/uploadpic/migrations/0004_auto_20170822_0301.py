# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-22 03:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploadpic', '0003_auto_20170822_0300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='img',
            name='test',
            field=models.CharField(default='', max_length=128, verbose_name='Just for test'),
        ),
    ]
