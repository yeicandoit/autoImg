# -*- coding: utf-8 -*-
import os
import myEmail
import autoImg
import datetime
import sqlite3
import random
import traceback
from time import sleep

def run_shell(cmd):
    if 0 != os.system(cmd):
        print "Execute " + cmd + " error, exit"
        exit(0)

dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活']}

def ptu():
    today = datetime.date.today().strftime('%Y-%m-%d')

    #Sqlite saved the ad demand
    conn = sqlite3.connect('webAutoImg/db.sqlite3')
    cc = conn.cursor()
    print 'Opened database successfully'
    cursor = cc.execute('select app, adType, adImg, adCornerImg, wcType, network, time, battery, title, doc, id '
                        'from autoimage_addemand where date ="' + today + '" and status = 0')

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
            savepath = 'webAutoImg/media/composite/' + today + '-' + str(tId) + '.png'
            tPath = 'composite/' + today + '-' + str(tId) + '.png'

            was = dictWebAccount.get(wcType)
            wa = was[random.randint(0, len(was)-1)]
            ai = autoImg.AutoImg(time, battery, wa, adImg, adCornerImg, adType, network, title, doc, savepath)
            if ai.compositeImage():
                print "composite image OK!!!"
                cc.execute('update autoimage_addemand set compositeImage = "' +
                           tPath + '", status = 1 where id = ' + str(tId))
                conn.commit()
            else:
                content = 'Failed ad info is app:' + app + ' 广告类型:'.decode('utf-8') + adType \
                          + ' 广告:'.decode('utf-8') + adImg + ' 角标:'.decode('utf-8') + adCornerImg \
                          + ' 公众号类型:'.decode('utf-8') + wcType + ' 网络:'.decode('utf-8') + network \
                          + ' 时间:'.decode('utf-8') + time + ' 电量:'.decode('utf-8') + str(battery) \
                          + ' 标题:'.decode('utf-8') + title + ' 文案:'.decode('utf-8') + doc \
                          + ' sqlite id:' + str(tId)
                myEmail.send_email('wangqiang@optaim.com', content)
                print "Failed to composite image"
        else:
            print 'Only support weixin now'

    conn.close()

if __name__ == '__main__':
    try:
        while 1:
            ptu()
            sleep(3)
    except Exception as e:
        myEmail.send_email('wangqiang@optaim.com', 'mainActivity.py process failed!!!')
        traceback.print_exc()