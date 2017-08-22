# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class AdDemand(models.Model):
    app = models.CharField(max_length=64)
    adType = models.CharField(max_length=64)
    adImg = models.ImageField(upload_to='upload')
    adCornerImg = models.ImageField(null=True, upload_to='upload')
    wcType = models.CharField(max_length=64, null=True)
    network = models.CharField(max_length=64, null=True)
    time = models.CharField(max_length=64)
    battery = models.FloatField(null=True)
