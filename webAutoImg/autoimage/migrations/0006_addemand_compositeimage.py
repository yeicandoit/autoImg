# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-22 08:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoimage', '0005_addemand_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='addemand',
            name='compositeImage',
            field=models.ImageField(null=True, upload_to=b''),
        ),
    ]