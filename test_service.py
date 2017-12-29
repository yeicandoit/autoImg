# -*- coding: utf-8 -*-
import service
demands = [{
    u'adCornerType': 0,
    u'battery': 0.8,
    u'adImg': u'http://pic.optaim.com/picture/2017-12/151451408137211.jpg',
    u'app': u'jxedt',
    u'webAccount': u'汽车之家',
    u'logo': None,
    u'id': 1010,
    u'wcType': u'information',
    u'network': u'wifi',
    u'title': u'',
    u'create_userid': 596,
    u'email': u'wangqiang@optaim.com',
    u'status': 0,
    u'basemap': None,
    u'reqDate': u'2017-12-29 10:21:54',
    u'compositeImage': None,
    u'city': u'',
    u'finDate': None,
    u'doc': u'',
    u'advertiserid': 3833,
    u'doc1stLine': -1,
    u'time': u'10:28',
    u'adType': u'banner',
    u'os': u'android'
}]

if __name__ == '__main__':
    service.pImage(demands)