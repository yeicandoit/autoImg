# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from autoimage.models import AdDemand
from django.http import HttpResponse
import datetime

# Create your views here.
def savedemand(request):
    m_post = request.POST

    demand = AdDemand(app=m_post['app'], adType=m_post['adType'], adImg=request.FILES.get('adImg'),
                      adCornerImg=request.FILES.get('adCornerImg'), wcType=m_post['wcType'],
                      network=m_post['network'], time=m_post['time'], battery=float(m_post['battery']),
                      title=m_post['title'], doc=m_post['doc'], date=datetime.date.today().strftime('%Y-%m-%d'))
    demand.save()
    return HttpResponse("successful!!!")