# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.shortcuts import redirect
from autoimage.models import AdDemand
from django.http import HttpResponseRedirect
import datetime

# Create your views here.
def index(request):
    context = {}
    return render(request, 'autoimage/autoimage.html', context)

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
        context = {
            'color': 'red',
            'info': '请上传广告!!!',
        }
        return render(request, 'autoimage/autoimage.html', context)
    if None == ad_corner_img:
        ad_corner_img = 'ad_default/corner-mark.png'
    if None == ad_doc:
        ad_doc = ''
    if None == ad_title:
        ad_title = ''
    if '' == ad_time:
        context = {
            'color':'red',
            'info':'请设置时间!!!'
        }
        return render(request, 'autoimage/autoimage.html', context)

    demand = AdDemand(app=m_post['app'], adType=m_post['adType'], adImg=ad_img,
                      adCornerImg=ad_corner_img, wcType=m_post['wcType'],
                      network=m_post['network'], time=ad_time, battery=float(m_post['battery']),
                      title=ad_title, doc=ad_doc, date=datetime.date.today().strftime('%Y-%m-%d'),
                      status=0, doc1stLine=int(m_post['doc1stLine']))
    demand.save()
    return HttpResponseRedirect('/showimages')

def showimages(request):
    imgs = AdDemand.objects.filter(date = datetime.date.today().strftime('%Y-%m-%d'))
    context = {
        'imgs':imgs,
    }

    return render(request, 'autoimage/showimages.html', context)
