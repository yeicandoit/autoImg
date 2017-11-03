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
import hashlib
import requests
import util

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')
dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活', '汽车维修与保养', '汽车点评', '汽车知识攻略',
                         '汽车大师', '汽车头条', '汽车情报', '金鸽传媒', '优车生活', '摩托车杂志', '车闻速递', '30秒懂车',
                         '汽车天天资讯', '汽车公社', '砖说车', '车之家', '爱车一族', '车乐汽车技术交流', 'AC汽车后市场',
                         '街拍车模', '各地车友惠', '跑车世界', '开车小技巧', '深夜一人夜听', '爱车一派', '选车听我的',
                         '原创汽车改装吧', '斗车', '轿车情报'],
                  'finance':['金融投资报', '每日金融', '贸易金融'],
                  'house':['中国房地产报', '中国房地产', '新鲜居室', '霸都楼市', '装修家居风水', '家居布局大师',
                           '美式装修风格', '家居装修攻略', '房地产经纪', '商业地产V评论', '新中式装修风格设计', '私家园林',
                           '房闻天下', '室内装修样板间'],
                  'travel':['旅行家杂志', '最旅行', '户外探险outdoor'],
                  'information':['第一财经资讯', '新闻晨报', '新闻早餐', '新闻夜航', '冯站长之家', '占豪', '环球时报',
                                 '观察者网', '都市快报', '半岛晨报', '广告也震惊', '中国企业家杂志', '今启网', '鼎盛网',
                                 '热点阅览', '热门大参考', '头条新闻', '早间新|闻', '今日快消息', '羊城晚报', '智汇栏目',
                                 '时代春秋', '珍贵老照片'],
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
        city = row['city']
        savepath = 'webAutoImg/media/composite/' + today + '-' + str(tId) + '.png'
        wa = ''
        adCornerImg = ''

        suffix = os.path.splitext(row['adImg'])[1]
        adImg = 'webAutoImg/media/upload/' + today + '-' + str(tId) + suffix
        urllib.urlretrieve(row['adImg'], adImg)

        logo = ""
        if '' != row['logo']:
            try:
                suffix = os.path.splitext(row['logo'])[1]
                logo = 'webAutoImg/media/upload/' + today + '-logo-' + str(tId) + suffix
                urllib.urlretrieve(row['logo'], logo)
            except:
                pass

        if 'weixin' == app:
            if 0 == row['adCornerType']:  # 活动推广
                adCornerImg = 'ad_area/corner-mark.png'
            elif 1 == row['adCornerType']:  # 商品推广
                adCornerImg = 'ad_area/corner-mark-1.png'
            elif 2 == row['adCornerType']:  # 应用下载
                adCornerImg = 'ad_area/corner-mark-2.png'

            if webAccount:
                wa = webAccount
            else:
                if '' == wcType:
                    wcType = 'car';
                was = dictWebAccount.get(wcType)
                wa = was[random.randint(0, len(was)-1)].decode('utf-8')
            ai = autoImg.WebChatAutoImg(mtime, battery, wa, adImg, adCornerImg, adType, network,
                                        title, doc, doc1stLine, savepath)
        elif 'QQWeather' == app:
            adCornerImg = 'ad_area/corner-ad.png'
            ai = autoImg.QQAutoImg('weather', city, mtime, battery, adImg, adCornerImg, adType, network,
                                   title, doc, doc1stLine, savepath)
        elif 'QQBrowser' == app:
            ai = autoImg.QQBrowserAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                          title, doc, doc1stLine, savepath)
        elif 'QQDongtai' == app:
            ai = autoImg.QzoneAutoImg(mtime, battery, adImg, adCornerImg, adType, network, title,
                                   doc, doc1stLine, savepath, logo)
        elif 'qiushi' == app:
            ai = autoImg.QSBKAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                          title, doc, doc1stLine, savepath, logo)
        elif 'shuqi' == app:
            ai = autoImg.ShuQiAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                     title, doc, doc1stLine, savepath)
        elif 'iqiyi' == app:
            ai = autoImg.TianyaAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                     title, doc, doc1stLine, savepath)
        elif 'tianya' == app:
            ai = autoImg.TianyaAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                       title, doc, doc1stLine, savepath)
        else:
            ai = None
            parameters = {'id': tId, 'status': 2}
            requests.get(urlUpdate, headers=headers, params=parameters)
            if email:
                myEmail.send_email(email, '现在不支持此种截图'.decode('utf-8'))
            mStr = "Do not support %s now!!!" % (app)
            logger.info(mStr)
            continue

        ok, mType, msg = ai.compositeImage()
        if ok:
            logger.debug("composite image OK!!!")
            parameters = {'id': tId, 'status': 1}
            requests.get(urlUpdate, headers=headers, params=parameters)
            files = [savepath, 'screenshot.png']
            if email:
                myEmail.send_email(email, '若有问题，请联系王强：410342333'.decode('utf-8'), files)
        else:
            content = 'Failed ad info is<br> app:' + app + u'<br> 广告类型:' + adType \
                      + u'<br> 广告:' + adImg + u'<br> 角标:' + adCornerImg \
                      + u'<br> 公众号:' + wa + u'<br> 网络:' + network \
                      + u'<br> 时间:' + mtime + u'<br> 电量:' + str(battery) \
                      + u'<br> 标题:' + title + u'<br> 文案:' + doc \
                      + '<br> DB id:' + str(tId) + u'<br> 第一行文案长度:' + str(doc1stLine) \
                      + u'<br> 邮箱:' + email \
                      + u'<br><br>错误信息:' + msg
            myEmail.send_email('wangqiang@optaim.com', content)
            logger.warn("Failed to composite image:" + content)
            if autoImg.AutoImg.TYPE_ARG == mType:
                parameters = {'id': tId, 'status': 2}
                requests.get(urlUpdate, headers=headers, params=parameters)
                if email:
                    myEmail.send_email(email, msg)

if __name__ == '__main__':
    while 1:
        try:
            util.Honor8Awaken.awaken()
            ptu()
            time.sleep(10)
        except Exception as e:
            logger.error(traceback.format_exc())
            #If wifi is not connected, send_email will fail and this process will fail too, so do not send_email in Exception.
            #myEmail.send_email('wangqiang@optaim.com', 'mainActivity.py process failed!!!<br>' + traceback.format_exc())
            time.sleep(30)
