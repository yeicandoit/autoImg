# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from uploadpic.models import IMG

def upload(request):
    return render(request, 'uploadpic/upload.html')
def show(request):
    new_img = IMG(img=request.FILES.get('img'))
    new_img.save()
    content = {
        'aaa': new_img,
    }
    return render(request, 'uploadpic/show.html', content)
