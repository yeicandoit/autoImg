# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse

def hello(request):
    context = {}
    context['hello'] = 'Hello World!'
    return render(request, 'autoimage.html', context)

def imageDemand(request):
    if request.POST:
        m_post = request.POST
        str = m_post['app'] + " " + m_post['type'] + ' ' + m_post['wcType'] + ' ' + m_post['network'] + \
              " " + m_post['battery']
        return HttpResponse(str)
