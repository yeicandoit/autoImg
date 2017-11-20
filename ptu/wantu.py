#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
from base import Base

class WantuAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png'):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.img_ad_kai_flag = cv2.imread(self.cf.get('Wantu', 'img_ad_kai_flag'), 0)
        self.fp_ad_kai_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_kai_flag)))
        self.logger.debug("fp_ad_kai_flag:%s", self.fp_ad_kai_flag)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.wantu.activity',
            'appActivity': '.SplashScreenActivity',
            'udid': '192.168.56.101:5555',
        }

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        cnt = 10
        while 1:
            assert cnt != 20, "Do not find kai ad in wantu"
            self.driver.get_screenshot_as_file('screenshot.png')
            ok, _, _ = self.findMatchedArea(cv2.imread('screenshot.png', 0), self.img_ad_kai_flag, self.fp_ad_kai_flag)
            if ok:
                break
            sleep(1)

        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.cf.get('Wantu', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        img_color = cv2.imread('screenshot.png')
        img_color[0:ad_size[1], 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()


if __name__ == '__main__':
    try:
        autoImg = WantuAutoImg('11:49', 0.8, 'ads/640x330.jpg', '../ad_area/corner-ad.png',
                               'feeds_banner', '4G', u'吉利新帝豪', u'饼子还能这么吃，秒杀鸡蛋灌饼，完爆煎饼果子，做法还超级简单！')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
