#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image
import cv2
import imagehash
import traceback
import time
from base import Base

class Systemmanager(Base):
    def __init__(self):
        Base.__init__(self, '', 0, '', '', '', '', '', '')

        self.img_optimization = cv2.imread("ad_area/systemmanager/Honor8/optimization.png", 0)
        self.fp_optimization = str(imagehash.dhash(Image.fromarray(self.img_optimization)))
        self.logger.debug("fp_optimization:%s", self.fp_optimization)

        self.timestamp = int(time.time())
        self.device_udid = 'WTK7N16923009805'
        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '7.0',
            'deviceName': 'Honor8',
            'appPackage': 'com.huawei.systemmanager',
            'appActivity': '.mainscreen.MainScreenActivity',
            'udid': 'WTK7N16923009805',
        }

    def start(self):
        timestamp = int(time.time())
        # Clean honor8 every harf hour
        if timestamp - self.timestamp < 1800:
            return
        self.timestamp = timestamp
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(15)

        ok, tl, br = self.findElementPos4Awhile(self.img_optimization, self.fp_optimization)
        if ok:
            self.clickEliment(self.device_udid, tl[0], tl[1])
            sleep(10)

        self.driver.quit()

if __name__ == '__main__':
    try:
        autoImg = Systemmanager()
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
