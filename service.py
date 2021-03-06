# -*- coding: utf-8 -*-
import os
import datetime
import random
import traceback
import time
import logging
import hashlib
import requests
import subprocess
from util import myEmail
import autoImg
import ptu
from ptu import qnews

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')
dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活', '汽车维修与保养', '汽车点评', '汽车知识攻略',
                         '汽车大师', '汽车头条', '汽车情报', '金鸽传媒', '优车生活', '摩托车杂志', '车闻速递', '30秒懂车',
                         '汽车天天资讯', '汽车公社', '砖说车', '车之家', '爱车一族', '车乐汽车技术交流', 'AC汽车后市场',
                         '街拍车模', '各地车友惠', '跑车世界', '开车小技巧', '深夜一人夜听', '爱车一派', '选车听我的',
                         '原创汽车改装吧', '斗车', '轿车情报'],
                  'finance':['金融投资报', '每日金融', '贸易金融', '老铁股道', '股票早餐', 'Wind资讯', '二鸟说', '理财知识',
                             '资本论', '股票情报', '澄泓财经', '鸣金网', '金融内参', '千保网'],
                  'house':['中国房地产报', '中国房地产', '新鲜居室', '霸都楼市', '装修家居风水', '家居布局大师',
                           '美式装修风格', '家居装修攻略', '房地产经纪', '商业地产V评论', '新中式装修风格设计', '私家园林',
                           '房闻天下', '室内装修样板间'],
                  'travel':['旅行家杂志', '最旅行', '户外探险outdoor', '最美风景在路上', '盈科旅游', '她读精选', '带上音乐看山水',
                            '踏马行者', '88爱旅行', '旅游', '旅行', '喜欢旅行', '醉美黄山', '陪你去旅行', '全球热点旅游',
                            '旅游指南', '旅行攻略', '一起去旅行吧', '每日旅游', '户外旅行小指南'],
                  'information':['第一财经资讯', '新闻晨报', '新闻早餐', '新闻夜航', '冯站长之家', '占豪', '环球时报',
                                 '观察者网', '都市快报', '半岛晨报', '广告也震惊', '中国企业家杂志', '今启网', '鼎盛网',
                                 '热点阅览', '热门大参考', '头条新闻', '早间新|闻', '今日快消息', '羊城晚报', '智汇栏目',
                                 '时代春秋', '珍贵老照片'],
                  'game':['游戏日报'],
                  'ent':['冷笑话精选', '内部绝密', '爆笑短片', '十万个未解之谜', '搞笑视频', '幽默村老王', '激进的壁纸喵',
                         '女人男人', '老歌回味', '六点半', '小罗恶搞', '当时我就震惊了', '天天逗事']}
urlDemand = "http://dsp.optaim.com/api/picture/getautoimagedemand"
urlUpdate = "http://dsp.optaim.com/api/picture/updatestatus"
reqTimes= {} #Record times of every ad Ptu request, if times is bigger than 3, drop this ad request.

def run_shell(cmd):
    if 0 != os.system(cmd):
        logger.error("Execute " + cmd + " error, exit")
        #exit(0)

def loadImg(src, dest):
    cmd = "curl %s -o %s" %(src, dest)
    run_shell(cmd)

def pImage(test_data=None):
    today = datetime.date.today().strftime('%Y-%m-%d')
    timestamp = str(int(time.time()))
    authoration = hashlib.md5("zlkjdix827fhx_adfe" + timestamp).hexdigest()
    headers = {'Authorization': authoration, 'Timestamp': timestamp}
    # Set requests connect and read timeout before get
    r = requests.get(urlDemand, headers=headers, timeout=(5,10))
    rJson = r.json()
    logger.debug(r.json())
    if rJson['result'] == 0:
        demands = rJson['message']['demands']
    else:
        demands = []

    if None != test_data:
        demands = test_data

    for row in demands:
        if 'ios' == row['os']:
            continue
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

        adImgArr = row['adImg'].split(',')
        if len(adImgArr) == 1:
            suffix = os.path.splitext(row['adImg'])[1]
            adImg = 'webAutoImg/media/upload/' + today + '-' + str(tId) + suffix
            #urllib.urlretrieve(row['adImg'], adImg)
            loadImg(row['adImg'], adImg)
        else:
            adImg = ''
            for i in range(0, len(adImgArr)):
                suffix = os.path.splitext(adImgArr[i])[1]
                adImgPath = 'webAutoImg/media/upload/' + today + '-' + str(tId) + '-' + str(i) + suffix
                if i != len(adImgArr) - 1:
                    adImg += adImgPath + ','
                else:
                    adImg += adImgPath
                #urllib.urlretrieve(adImgArr[i], adImgPath)
                loadImg(adImgArr[i], adImgPath)


        #Record Ptu request time for this ad
        if reqTimes.has_key(tId):
            reqTimes[tId] += 1
        else:
            reqTimes[tId] = 1

        logo = ""
        if '' != row['logo']:
            try:
                suffix = os.path.splitext(row['logo'])[1]
                logo = 'webAutoImg/media/upload/' + today + '-logo-' + str(tId) + suffix
                #urllib.urlretrieve(row['logo'], logo)
                loadImg(row['logo'], logo)
            except:
                pass

        subject = u"自动P图"

        if 'weixin' == app:
            subject += u"-微信公众号-"
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
            subject += wa
            ai = autoImg.WebChatAutoImg(mtime, battery, wa, adImg, adCornerImg, adType, network,
                                       title, doc, doc1stLine, savepath)
        elif 'QQWeather' == app:
            subject += u"-QQ天气"
            adCornerImg = 'ad_area/corner-ad.png'
            ai = autoImg.QQAutoImg('weather', city, mtime, battery, adImg, adCornerImg, adType, network,
                                    title, doc, doc1stLine, savepath)
        elif 'QQBrowser' == app:
            subject += u"-QQ浏览器"
            ai = ptu.qqbrowser.QQBrowserAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                    title, doc, doc1stLine, savepath)
        elif 'QQDongtai' == app:
            subject += u"-QQ空间"
            ai = autoImg.QzoneAutoImg(mtime, battery, adImg, adCornerImg, adType, network, title,
                                   doc, doc1stLine, savepath, logo)
        elif 'qiushi' == app:
            subject += u"-糗事百科"
            ai = autoImg.QSBKAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                    title, doc, doc1stLine, savepath, logo)
        elif 'shuqi' == app:
            subject += u"-书旗小说"
            ai = autoImg.ShuQiAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                     title, doc, doc1stLine, savepath)
        elif 'tianya' == app:
            subject += u"-天涯论坛"
            ai = autoImg.TianyaAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                       title, doc, doc1stLine, savepath)
        elif 'qnews' == app:
            subject += u"-腾讯新闻"
            ai = qnews.QnewsAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                    title, doc, doc1stLine, savepath)
        elif 'wantu' == app:
            subject += u"-玩图"
            ai = ptu.wantu.WantuAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                        title, doc, doc1stLine, savepath, logo)
        #TODO have not found related ad
        # elif 'hers' == app:
        #    ai = ptu.hers.HersAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
        #                                title, doc, doc1stLine, savepath, logo)
        elif 'calendar' == app:
            subject += u"-万年历"
            ai = ptu.calendar.CalendarAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                      title, doc, doc1stLine, savepath)
        elif 'meiyancamera' == app:
            subject += u"-美颜相机"
            ai = ptu.meiyancamera.MeiyancameraAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                                    title, doc, doc1stLine, savepath)
        elif 'batterydoctor' == app:
            subject += u"-金山电池医生"
            ai = ptu.batterydoctor.BatteryDoctorAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                                        title, doc, doc1stLine, savepath)
        elif 'esbook' == app:
            subject += u"-宜搜小说"
            ai = ptu.esbook.EsbookAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                            title, doc, doc1stLine, savepath)
        elif 'jxedt' == app:
            subject += u"-驾校一点通"
            ai = ptu.jxedt.JxedtAutoImg(mtime, battery, adImg, adCornerImg, adType, network,
                                          title, doc, doc1stLine, savepath)
        else:
            parameters = {'id': tId, 'status': 2}
            requests.get(urlUpdate, headers=headers, params=parameters)
            if email:
                myEmail.send_email(email, '现在不支持此种截图'.decode('utf-8'))
            mStr = "Do not support %s now!!!" % (app)
            logger.info(mStr)
            if reqTimes.has_key(tId):
                del reqTimes[tId]
            continue

        ok, mType, msg = ai.compositeImage()
        if ok:
            logger.debug("composite image OK!!!")
            parameters = {'id': tId, 'status': 1}
            requests.get(urlUpdate, headers=headers, params=parameters)
            files = [savepath, 'screenshot.png']
            if reqTimes.has_key(tId):
                del reqTimes[tId]
            if email:
                subject += u"-成功"
                myEmail.send_email(email, '若有问题，请联系王强：410342333'.decode('utf-8'), files, subject)
        else:
            content = 'Failed ad info is<br> app:' + app + u'<br> 广告类型:' + adType \
                      + u'<br> 广告:' + adImg + u'<br> 角标:' + adCornerImg \
                      + u'<br> 公众号:' + wa + u'<br> 网络:' + network \
                      + u'<br> 时间:' + mtime + u'<br> 电量:' + str(battery) \
                      + u'<br> 标题:' + title + u'<br> 文案:' + doc \
                      + '<br> DB id:' + str(tId) + u'<br> 第一行文案长度:' + str(doc1stLine) \
                      + u'<br> 邮箱:' + email \
                      + u'<br><br>错误信息:'
            try:
                #msg may contain some Chinese words that could not parse
                content += msg
            except:
                pass
            subject += u"-失败"
            myEmail.send_email('wangqiang@optaim.com', content, subject=subject)
            logger.warn("Failed to composite image:" + content)
            #If parameters err or has failed 3 times for this ad Ptu request
            if (reqTimes.has_key(tId) and reqTimes[tId] >= 3) or autoImg.AutoImg.TYPE_ARG == mType:
                parameters = {'id': tId, 'status': 2}
                requests.get(urlUpdate, headers=headers, params=parameters)
                if reqTimes.has_key(tId):
                    if reqTimes[tId] >= 3:
                        msg = u'您的P图请求没有完成，若是微信公众号P图请求并指定了公众号，请更换其他公众号试试；其他P图请求失败，请' \
                              u'联系相关负责人！'
                    del reqTimes[tId]
                if email:
                    myEmail.send_email(email, msg, subject=subject)


if __name__ == '__main__':
    subprocess.Popen("python util/monitor.py", shell=True)
    cnt = 0
    while 1:
        cnt += 1
        try:
            #util.Honor8Awaken.awaken()
            #Clean honor8 every harf hour
            ptu.mHonor8Clean.compositeImage()
            #Clean android simulator memory about every 5 minutes
            ptu.memClean.compositeImage()
            pImage()
            time.sleep(10)
        except Exception as e:
            logger.error(traceback.format_exc())
            #If wifi is not connected, send_email will fail and this process will fail too, so do not send_email in Exception.
            #myEmail.send_email('wangqiang@optaim.com', 'mainActivity.py process failed!!!<br>' + traceback.format_exc())
            time.sleep(30)
