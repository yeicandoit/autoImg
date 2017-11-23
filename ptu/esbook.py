#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
from base import Base

class EsbookAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.esbook.reader',
            'appActivity': '.activity.ActLoading',
            'udid': '192.168.56.101:5555',
        }

    def assembleFeedsAd(self):
        pass

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(10)


        self.driver.quit()


if __name__ == '__main__':
    try:
        autoImg = EsbookAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100', logo='ads/logo.jpg')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
