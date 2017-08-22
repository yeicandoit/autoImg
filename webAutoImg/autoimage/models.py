# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class AdDemand(models.Model):
    app = models.CharField(max_length=64)
    adType = models.CharField(max_length=64)
    adImg = models.ImageField(upload_to='upload')
    adCornerImg = models.ImageField(null=True, upload_to='upload')
    title = models.CharField(max_length=128, null=True)
    doc = models.CharField(max_length=128, null=True)
    wcType = models.CharField(max_length=64, null=True)
    network = models.CharField(max_length=64, null=True)
    time = models.CharField(max_length=64)
    battery = models.FloatField(null=True)
    date = models.DateField()
    status = models.IntegerField()
    compositeImage = models.ImageField(null=True)
