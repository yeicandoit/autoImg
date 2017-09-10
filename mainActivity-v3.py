# -*- coding: utf-8 -*-
import os
import myEmail
import autoImg
import datetime
import random
import traceback
import time
import logging
import urllib
import mainActivity
import hashlib
import requests

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')
dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活', '汽车维修与保养', '汽车点评', '汽车知识攻略',
                         '汽车大师', '汽车头条', '汽车情报'],
                  'finance':['金融投资报', '每日金融', '贸易金融'],
                  'house':['中国房地产报', '中国房地产'],
                  'travel':['旅行家杂志', '最旅行', '户外探险outdoor'],
                  'information':['第一财经资讯', '新闻晨报', '新闻早餐', '新闻夜航'],
                  'game':['游戏日报']}
urlDemand = "http://dsp.optaim.com/api/picture/getautoimagedemand"
urlUpdate = "http://dsp.optaim.com/api/picture/updatestatus"

def run_shell(cmd):
    if 0 != os.system(cmd):
        logger.error("Execute " + cmd + " error, exit")
        exit(0)

def ptu():
    today = datetime.date.today().strftime('%Y-%m-%d')
    timestamp = str(int(time.time()))
    authoration = hashlib.md5("zlkjdix827fhx_adfe" + timestamp).hexdigest()
    headers = {'Authorization': authoration, 'Timestamp': timestamp}
    r = requests.get(urlDemand, headers=headers)
    rJson = r.json()
    logger.debug(r.json())
    if rJson['result'] == 0:
        demands = rJson['message']['demands']
    else:
        demands = []

    for row in demands:
        app = row['app']
        if 'weixin' == app:
            adType = row['adType']
            wcType = row['wcType']
            network = row['network']
            mtime = row['time']
            battery = row['battery']
            title = row['title']
            doc = row['doc']
            tId = row['id']
            doc1stLine = row['doc1stLine']
            email = row['email']
            webAccount = row['webAccount']
            savepath = 'webAutoImg/media/composite/' + today + '-' + str(tId) + '.png'

            suffix = os.path.splitext(row['adImg'])[1]
            adImg = 'webAutoImg/media/upload/' + today + '-' + str(tId) + suffix
            urllib.urlretrieve(row['adImg'], adImg)
            if 0 == row['adCornerType']: #活动推广
                adCornerImg = 'ad_area/corner-mark.png'
            else: #商品推广
                adCornerImg = 'ad_area/corner-mark-1.png'

            if webAccount:
                wa = webAccount
            else:
                was = dictWebAccount.get(wcType)
                wa = was[random.randint(0, len(was)-1)].decode('utf-8')
            ai = autoImg.WebChatAutoImg(mtime, battery, wa, adImg, adCornerImg, adType, network,
                                 title, doc, doc1stLine, savepath)
            if ai.compositeImage():
                logger.debug("composite image OK!!!")
                parameters = {'id': tId, 'status': 1}
                requests.get(urlUpdate, headers=headers, params=parameters)
                if email:
                    myEmail.send_email(email, '若有问题，请联系王强：410342333'.decode('utf-8'), savepath)
            else:
                content = 'Failed ad info is<br> app:' + app + u'<br> 广告类型:' + adType \
                          + u'<br> 广告:' + adImg + u'<br> 角标:' + adCornerImg \
                          + u'<br> 公众号:' + wa + u'<br> 网络:' + network \
                          + u'<br> 时间:' + mtime + u'<br> 电量:' + str(battery) \
                          + u'<br> 标题:' + title + u'<br> 文案:' + doc \
                          + '<br> DB id:' + str(tId) + u'<br> 第一行文案长度:' + str(doc1stLine) \
                          + u'<br> 邮箱:' + email
                myEmail.send_email('wangqiang@optaim.com', content)
                logger.warn("Failed to composite image:" + content)
        else:
            logger.warn('Only support weixin now')

if __name__ == '__main__':
    try:
        while 1:
            ptu()
            mainActivity.ptu()
            time.sleep(10)
    except Exception as e:
        logger.error(traceback.format_exc())
        myEmail.send_email('wangqiang@optaim.com', 'mainActivity.py process failed!!!<br>' + traceback.format_exc())
