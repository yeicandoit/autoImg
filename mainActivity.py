# -*- coding: utf-8 -*-
import os
import myEmail
import autoImg
import datetime
import sqlite3
import random
import traceback
from time import sleep
import logging
import logging.config

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')
dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活', '汽车维修与保养', '汽车点评', '汽车知识攻略',
                         '汽车大师', '汽车头条', '汽车情报'],
                  'finance':['金融投资报', '每日金融', '贸易金融'],
                  'house':['中国房地产报', '中国房地产'],
                  'travel':['旅行家杂志', '最旅行', '户外探险outdoor'],
                  'information':['第一财经资讯', '新闻晨报', '新闻早餐', '新闻夜航'],
                  'game':['游戏日报']}

def run_shell(cmd):
    if 0 != os.system(cmd):
        logger.error("Execute " + cmd + " error, exit")
        exit(0)

def ptu():
    today = datetime.date.today().strftime('%Y-%m-%d')

    #Sqlite saved the ad demand
    conn = sqlite3.connect('webAutoImg/db.sqlite3')
    cc = conn.cursor()
    logger.debug('Opened database successfully')
    cursor = cc.execute('select app, adType, adImg, adCornerImg, wcType, network, time, battery, title, doc, id, '
                        'doc1stLine, email from autoimage_addemand where date ="' + today + '" and status = 0')

    for row in cursor:
        app = row[0]
        if 'weixin' == app:
            adType = row[1]
            adImg ='webAutoImg/media/' + row[2]
            adCornerImg = 'webAutoImg/media/' + row[3]
            wcType = row[4]
            network = row[5]
            time = row[6]
            battery = row[7]
            title = row[8]
            doc = row[9]
            tId = row[10]
            doc1stLine = row[11]
            email = row[12]
            savepath = 'webAutoImg/media/composite/' + today + '-' + str(tId) + '.png'
            tPath = 'composite/' + today + '-' + str(tId) + '.png'

            was = dictWebAccount.get(wcType)
            wa = was[random.randint(0, len(was)-1)]
            ai = autoImg.AutoImg(time, battery, wa, adImg, adCornerImg, adType, network, title, doc, doc1stLine, savepath)
            if ai.compositeImage():
                logger.debug("composite image OK!!!")
                cc.execute('update autoimage_addemand set compositeImage = "' +
                           tPath + '", status = 1 where id = ' + str(tId))
                conn.commit()
                if email:
                    myEmail.send_email(email, '若有问题，请联系王强：410342333'.decode('utf-8'), savepath)
            else:
                content = 'Failed ad info is<br> app:' + app + '<br> 广告类型:'.decode('utf-8') + adType \
                          + '<br> 广告:'.decode('utf-8') + adImg + '<br> 角标:'.decode('utf-8') + adCornerImg \
                          + '<br> 公众号:'.decode('utf-8') + wa.decode('utf-8') + '<br> 网络:'.decode('utf-8') + network \
                          + '<br> 时间:'.decode('utf-8') + time + '<br> 电量:'.decode('utf-8') + str(battery) \
                          + '<br> 标题:'.decode('utf-8') + title + '<br> 文案:'.decode('utf-8') + doc \
                          + '<br> sqlite id:' + str(tId) + '<br> 第一行文案长度:'.decode('utf-8') + str(doc1stLine) \
                          + '<br> 邮箱:'.decode('utf8') + email
                myEmail.send_email('wangqiang@optaim.com', content)
                logger.warn("Failed to composite image:" + content)
        else:
            logger.warn('Only support weixin now')

    conn.close()

if __name__ == '__main__':
    try:
        while 1:
            ptu()
            sleep(3)
    except Exception as e:
        logger.error(traceback.format_exc())
        myEmail.send_email('wangqiang@optaim.com', 'mainActivity.py process failed!!!<br>' + traceback.format_exc())