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
dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活']}

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
                        'doc1stLine from autoimage_addemand where date ="' + today + '" and status = 0')

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
            else:
                content = 'Failed ad info is<br> app:' + app + '<br> 广告类型:'.decode('utf-8') + adType \
                          + '<br> 广告:'.decode('utf-8') + adImg + '<br> 角标:'.decode('utf-8') + adCornerImg \
                          + '<br> 公众号:'.decode('utf-8') + wa.decode('utf-8') + '<br> 网络:'.decode('utf-8') + network \
                          + '<br> 时间:'.decode('utf-8') + time + '<br> 电量:'.decode('utf-8') + str(battery) \
                          + '<br> 标题:'.decode('utf-8') + title + '<br> 文案:'.decode('utf-8') + doc \
                          + '<br> sqlite id:' + str(tId) + '<br> 第一行文案长度:'.decode('utf-8') + str(doc1stLine)
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