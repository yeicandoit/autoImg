# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-29 02:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoimage', '0007_addemand_doc1stline'),
    ]

    operations = [
        migrations.AddField(
            model_name='addemand',
            name='email',
            field=models.CharField(max_length=64, null=True),
        ),
    ]