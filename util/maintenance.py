# -*- coding: utf-8 -*-

import time
import hashlib
import requests
import json

urlDemand = "http://dsp.optaim.com/api/picture/getautoimagedemand"
urlUpdate = "http://dsp.optaim.com/api/picture/updatestatus"
urlBasemap = "http://dsp.optaim.com/api/picture/updatebasemap"

def getHeaders():
    timestamp = str(int(time.time()))
    authoration = hashlib.md5("zlkjdix827fhx_adfe" + timestamp).hexdigest()
    headers = {'Authorization': authoration, 'Timestamp': timestamp}

    return headers

def getAutoimagedemand():
    res = requests.get(urlDemand, headers=getHeaders())
    print res.json()

def updatePtu(id, status=0):
    parameters = {'id': id, 'status': status}
    res = requests.get(urlUpdate, headers=getHeaders(), params=parameters)
    print res.json()

def updateBasemap(arr):
    data = json.dumps(arr)
    param = {'arrays': data}
    r = requests.get(urlBasemap, headers=getHeaders(), params=param)
    print r.json()
    #print r.reason

if __name__ == '__main__':
    #updatePtu(10, 1)
    arr = [
        {'os': 'ios', 'app': 'weixin', 'adType': 'banner'},
        {'os': 'ios', 'app': 'weixin', 'adType': 'image_text'},
        {'os': 'ios', 'app': 'weixin', 'adType': 'fine_big'},
        {'os': 'ios', 'app': 'QQWeather', 'adType': ''},
        {'os': 'ios', 'app': 'qnews', 'adType': 'feeds_big'},
        {'os': 'ios', 'app': 'qnews', 'adType': 'feeds_small'},
        {'os': 'ios', 'app': 'qnews', 'adType': 'feeds_multi'},
    ]
    updateBasemap(arr)


