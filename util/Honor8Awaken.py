from appium import webdriver
import time
import myEmail
import logging
logger = logging.getLogger('main.Honor8Awaken')

def awaken():
    desired_caps = {
        'platformName': 'Android',
        'platformVersion': '7.0',
        'deviceName': 'Honor8',
        'appPackage': 'com.tencent.mtt',
        'appActivity': '.MainActivity',
        'udid': 'WTK7N16923009805',
    }

    internal = timestamp = int(time.time())
    try:
        with open('/Users/iclick/wangqiang/autoImg//tmp_img/timestamp') as f:
            timestamp_ = [int(x) for x in f.readline().split()][0]
            internal -= timestamp_
            logger.debug ("%d, %d, %d", timestamp_, internal, timestamp)
    except:
        with open('/Users/iclick/wangqiang/autoImg//tmp_img/timestamp', 'w') as f:
            f.write(str(0))


    if 200 < internal:
        with open('/Users/iclick/wangqiang/autoImg//tmp_img/timestamp', 'w') as f:
            f.write(str(timestamp))
        driver = None
        try:
            driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
            driver.implicitly_wait(10)
            time.sleep(2)
            driver.quit()
        except:
            logger.debug("There is something wrong for Honor8")
            myEmail.send_email("wangqiang@optaim.com", u'There is something wrong for Honor8')
            if None != driver:
                driver.quit()

if __name__ == '__main__':
    awaken()