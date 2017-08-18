import os
import myEmail
import autoImg
import ConfigParser
import time

today = time.strftime('%Y-%m-%d',time.localtime(time.time()))
if myEmail.get_mails('test_email', today) == False:
    print 'Find no ad demand today, exit!!'
    exit(0)

ad_demand_zip = "ad_demand.zip"
ad_return = today + "_ad"
cmd = "unzip " + ad_demand_zip + "; mkdir -p " + ad_return
if 0 != os.system(cmd):
    print "Execute " + cmd + " error, exit"
    exit(0)

cf = ConfigParser.ConfigParser()
conf_path = "ad_demand/demand"
cf.read(conf_path);
for sec in cf.sections():
    time = cf.get(sec, 'time')
    battory = cf.getfloat(sec, 'battory')
    webaccount = cf.get(sec, 'webaccount')
    ad = cf.get(sec, 'ad')
    corner = cf.get(sec, 'corner')
    type = cf.get(sec, 'type')
    network = cf.get(sec, 'network')
    title = cf.get(sec, 'title')
    doc = cf.get(sec, 'doc')
    savePath = ad_return + '/' +  sec + '.png'
    ai = autoImg.AutoImg(time, battory, webaccount, ad, corner, type, network, title, doc, savePath)
    ai.start()

cmd = "mv " + today + "* finished/; rm ad_demand.zip; rm *.png; mv ad_demand finished/" + today
if 0 != os.system(cmd):
    print "Execute " + cmd + " error, exit"
    exit(0)
