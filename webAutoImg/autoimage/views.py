# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from autoimage.models import AdDemand
from django.http import HttpResponseRedirect
import datetime
import time
import os

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
    else:
        #时间举例(要用英文输入法输入)：09:01, 18:56
        ok = True
        if 5 != len(ad_time):
            ok = False
        for ch in ad_time:
            if ch < '\u0030' or ch > '\u003a':
                ok = False
        if False == ok:
            context = {
                'color': 'red',
                'info': '时间格式不正确!!!'
            }
            return render(request, 'autoimage/autoimage.html', context)
    if None == m_post['doc1stLine'] or '' == m_post['doc1stLine']:
        doc_1st_line = -1
    else:
        doc_1st_line = int(m_post['doc1stLine'])

    demand = AdDemand(app=m_post['app'], adType=m_post['adType'], adImg=ad_img,
                      adCornerImg=ad_corner_img, wcType=m_post['wcType'],
                      network=m_post['network'], time=ad_time, battery=float(m_post['battery']),
                      title=ad_title, doc=ad_doc, date=datetime.date.today().strftime('%Y-%m-%d'),
                      status=0, doc1stLine=doc_1st_line, email=m_post['email'])
    ext = '-ad' + os.path.splitext(demand.adImg.name)[1]
    demand.adImg.name = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time())) + ext
    if demand.adCornerImg.name != 'ad_default/corner-mark.png':
        demand.adCornerImg.name = 'corner-mark.png'
    demand.save()
    return HttpResponseRedirect('/showimages')

def showimages(request):
    imgs = AdDemand.objects.filter(date = datetime.date.today().strftime('%Y-%m-%d'))
    context = {
        'imgs':imgs,
    }

    return render(request, 'autoimage/showimages.html', context)
