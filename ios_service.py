# -*- coding: utf-8 -*-
import os
import datetime
import time
import json
import traceback
import logging
import logging.config
import hashlib
import requests
from util import myEmail, shareImg
from ptu import wechat, base, qnews, qqweather

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')
urlDemand = "http://dsp.optaim.com/api/picture/getautoimagedemand"
urlUpdate = "http://dsp.optaim.com/api/picture/updatestatus"
reqTimes= {} #Record times of every ad Ptu request, if times is bigger than 3, drop this ad request.

IPHONE = 1
IPHONE_PLUS = 2

phone_type_hash = {
    IPHONE: 'iPhone',
    IPHONE_PLUS: 'iPhone plus',
}

info_hash = {
    'common':{
        'config':{
            IPHONE: 'conf/iphone6.conf',
            IPHONE_PLUS: 'conf/iphone-plus.conf'
        }
    },
    'weixin':{
        'func':wechat.WechatAutoImgBg,
        'subject':u"-微信公众号-",
        'config':{
            IPHONE:'conf/wechat_iphone6.conf',
            IPHONE_PLUS:'conf/wechat_iphone-plus.conf',
        }
    },
    'QQWeather':{
        'func':qqweather.QQWeatherBg,
        'subject':u'-QQ天气-',
        'config':{
            IPHONE:'conf/qqweather_iphone6.conf',
        },
    },
    'qnews':{
        'func':qnews.QnewsAutoImgBg,
        'subject':u'-腾讯新闻客户端-',
        'config':{
            IPHONE:'conf/qnews_iphone6.conf',
        },
    },
}

def run_shell(cmd):
    if 0 != os.system(cmd):
        logger.error("Execute " + cmd + " error, exit")

def loadImg(src, dest):
    cmd = "curl %s -o %s" %(src, dest)
    run_shell(cmd)

def setParams(req):
    ok = True
    today = datetime.date.today().strftime('%Y-%m-%d')
    params = {}
    tId = req['id']
    params['adType'] = req['adType']
    params['adCornerType'] = req['adCornerType']
    params['wcType'] = req['wcType']
    params['network'] = req['network']
    params['time'] = req['time']
    params['battery'] = req['battery']
    params['title'] = req['title']
    params['doc'] = req['doc']
    params['webAccount'] = req['webAccount']
    params['city'] = req['city']
    savepath = 'webAutoImg/media/composite/' + today + '-' + str(tId) + '.png'
    params['savePath'] = savepath

    adImgArr = req['adImg'].split(',')
    if len(adImgArr) == 1:
        suffix = os.path.splitext(req['adImg'])[1]
        params['adImg'] = 'webAutoImg/media/upload/' + today + '-' + str(tId) + suffix
        # urllib.urlretrieve(row['adImg'], adImg)
        loadImg(req['adImg'], params['adImg'])
    else:
        params['adImg'] = ''
        for i in range(0, len(adImgArr)):
            suffix = os.path.splitext(adImgArr[i])[1]
            adImgPath = 'webAutoImg/media/upload/' + today + '-' + str(tId) + '-' + str(i) + suffix
            if i != len(adImgArr) - 1:
                params['adImg'] += adImgPath + ','
            else:
                params['adImg'] += adImgPath
            # urllib.urlretrieve(adImgArr[i], adImgPath)
            loadImg(adImgArr[i], adImgPath)

    if '' != req['logo']:
        try:
            suffix = os.path.splitext(req['logo'])[1]
            params['logo'] = 'webAutoImg/media/upload/' + today + '-logo-' + str(tId) + suffix
            # urllib.urlretrieve(row['logo'], logo)
            loadImg(req['logo'], params['logo'])
        except:
            pass
    if None != req['basemap']:
        suffix = os.path.splitext(req['basemap'])[1]
        params['basemap'] = 'webAutoImg/media/background/' + today + '-bg-' + str(tId) + suffix
        # urllib.urlretrieve(row['logo'], logo)
        params['basemap'] = req['basemap']
        #loadImg(req['basemap'], params['basemap'])
        w,h = base.Base.getImgWH(params['basemap'])
        if 750 == w and 1334 == h:  #iphone size
            params['conf'] = info_hash['common']['config'][IPHONE]
            params['config'] = info_hash[req['app']]['config'][IPHONE]
        else: #iphone-plus size
            params['conf'] = info_hash['common']['config'][IPHONE_PLUS]
            params['config'] = info_hash[req['app']]['config'][IPHONE_PLUS]
    else:
        params['conf'] = info_hash['common']['config'][req['phone_type']]
        params['config'] = info_hash[req['app']]['config'][req['phone_type']]
        params['basemap'] = shareImg.getImage(req['app'], req['adType'], phone_type_hash[req['phone_type']])
        if None == params['basemap']:
            ok = False
            logger.warning('No basemap for this request')

    logger.info("params is %s", json.dumps(params))

    return params, ok

def pImage(test_data=None):
    demands = []
    headers = {}
    if None != test_data:
        demands = test_data
    else:
        timestamp = str(int(time.time()))
        authoration = hashlib.md5("zlkjdix827fhx_adfe" + timestamp).hexdigest()
        headers = {'Authorization': authoration, 'Timestamp': timestamp}
        # Set requests connect and read timeout before get
        r = requests.get(urlDemand, headers=headers, timeout=(5,10))
        rJson = r.json()
        logger.debug(r.json())
        if rJson['result'] == 0:
            demands = rJson['message']['demands']

    for row in demands:
        if 'android' == row['os']:
            logger.info('Do not handle android auto P in ios_service.py')
            continue

        tId = row['id']
        email = row['email']
        params, ok = setParams(row)

        #Record Ptu request time for this ad
        if reqTimes.has_key(tId):
            reqTimes[tId] += 1
        else:
            reqTimes[tId] = 1
        subject = u"自动P图"
        if info_hash.has_key(row['app']) and ok:
            ai = info_hash[row['app']]['func'](params)
            if info_hash.has_key(row['app']):
                subject += info_hash[row['app']]['subject']
        else:
            parameters = {'id': tId, 'status': 2}
            requests.get(urlUpdate, headers=headers, params=parameters)
            if email:
                myEmail.send_email(email, '自动截图失败'.decode('utf-8'), subject=subject)
            mStr = "Do not support %s now!!!" % (row['app'])
            logger.info(mStr)
            if reqTimes.has_key(tId):
                del reqTimes[tId]
            continue

        ok, mType, msg = ai.compositeImage()
        if ok:
            logger.debug("composite image OK!!!")
            parameters = {'id': tId, 'status': 1}
            requests.get(urlUpdate, headers=headers, params=parameters)
            files = [params['savePath'], params['basemap']]
            if reqTimes.has_key(tId):
                del reqTimes[tId]
            if email:
                subject += u"-成功"
                myEmail.send_email(email, '若有问题，请联系王强：410342333'.decode('utf-8'), files, subject)
        else:
            content = u"Failed ad info is<br> app:%s, <br> 广告类型:%s, <br> 广告:%s, <br> 网络:%s, <br> 时间:%s, " \
                      u"<br> 电量:%s, <br> 标题:%s, <br> 文案:%s, <br> DB id:%d, <br> 邮箱:%s, <br><br>错误信息:" \
                      %(row['app'], row['adType'], row['adImg'], row['network'], row['time'], row['battery'],
                        row['title'], row['doc'], tId, row['email'])
            try:
                #msg may contain some Chinese words that could not parse
                content += msg
            except:
                pass
            subject += u"-失败"
            myEmail.send_email('wangqiang@optaim.com', content, subject=subject)
            logger.warn("Failed to composite image:" + content)
            #If parameters err or has failed 3 times for this ad Ptu request
            if (reqTimes.has_key(tId) and reqTimes[tId] >= 8) or base.Base.TYPE_ARG == mType:
                parameters = {'id': tId, 'status': 2}
                requests.get(urlUpdate, headers=headers, params=parameters)
                if reqTimes.has_key(tId):
                    if reqTimes[tId] >= 8:
                        msg = u'您的P图请求没有完成，若是微信公众号P图请求并指定了公众号，请更换其他公众号试试；其他P图请求失败，请' \
                              u'联系相关负责人！'
                    del reqTimes[tId]
                if email:
                    myEmail.send_email(email, msg, subject=subject)


if __name__ == '__main__':
    while 1:
        try:
            pImage()
            time.sleep(1)
        except:
            logger.error(traceback.format_exc())
