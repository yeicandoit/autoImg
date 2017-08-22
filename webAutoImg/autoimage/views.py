# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from autoimage.models import AdDemand
from django.http import HttpResponse
import datetime

# Create your views here.
def savedemand(request):
    m_post = request.POST

    #Check the POST args overall, then mainActivity.py will not check args
    #Considerred templates/autoimage.html, we should only check adImg, adCornerImg, doc, title, time.
    ad_img = request.FILES.get('adImg')
    ad_corner_img = request.FILES.get('adCornerImg')
    ad_doc = m_post['doc']
    ad_title = m_post['title']
    ad_time = m_post['time']
    if None == ad_img:
        return HttpResponse('请上传广告')
    if None == ad_corner_img:
        ad_corner_img = 'ad_default/corner-mark.png'
    if None == ad_doc:
        ad_doc = ''
    if None == ad_title:
        ad_title = ''
    if '' == ad_time:
        return HttpResponse("请设置时间")

    demand = AdDemand(app=m_post['app'], adType=m_post['adType'], adImg=ad_img,
                      adCornerImg=ad_corner_img, wcType=m_post['wcType'],
                      network=m_post['network'], time=ad_time, battery=float(m_post['battery']),
                      title=ad_title, doc=ad_doc, date=datetime.date.today().strftime('%Y-%m-%d'),
                      status=0)
    demand.save()
    return HttpResponse("上传成功!!!")