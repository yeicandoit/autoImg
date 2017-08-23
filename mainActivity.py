# -*- coding: utf-8 -*-
import os
import myEmail
import autoImg
import time
import sqlite3
import random

def run_shell(cmd):
    if 0 != os.system(cmd):
        print "Execute " + cmd + " error, exit"
        exit(0)

dictWebAccount = {'car':['汽车之家', '汽车工艺师', '汽车生活', '车云']}

#Get ad demand from email
today = time.strftime('%Y-%m-%d',time.localtime(time.time()))

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
            print "Failed to composite image"
    else:
        print 'Only support weixin now'

conn.close()
#myEmail.send_email(ad_return_zip, 'wangqiang@optaim.com')

#Remove files useless, move ads to specified dir.
#cmd = "rm " + ad_return_zip + " *.png ad_demand.zip; mv " + ad_return + " finished/; mv ad_demand finished/" + today
#run_shell(cmd)

