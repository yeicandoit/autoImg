#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image
import cv2
import imagehash
import traceback
from base import Base

class BatteryDoctorAutoImg(Base):
    def __init__(self, time='', battery=1, img_paste_ad='', img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png'):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        if 'kai' == self.ad_type:
            self.img_ad_kai_flag = cv2.imread(self.cf.get('BatteryDoctor', 'img_ad_kai_flag'), 0)
            self.fp_ad_kai_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_kai_flag)))
            self.logger.debug("fp_ad_kai_flag:%s", self.fp_ad_kai_flag)

        if 'banner' == self.ad_type:
            self.img_ad_banner_flag = cv2.imread(self.cf.get('BatteryDoctor', 'img_ad_banner_flag'), 0)
            self.fp_ad_banner_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_banner_flag)))
            self.img_charge = cv2.imread(self.cf.get('BatteryDoctor', 'img_charge'), 0)
            self.fp_charge = str(imagehash.dhash(Image.fromarray(self.img_charge)))
            self.logger.debug("fp_ad_banner_flag:%s, fp_charge:%s", self.fp_ad_banner_flag, self.fp_charge)

        if 'check' == self.ad_type:
            self.img_save = cv2.imread(self.cf.get('BatteryDoctor', 'img_save'), 0)
            self.fp_save = str(imagehash.dhash(Image.fromarray(self.img_save)))
            self.logger.debug("fp_save:%s", self.fp_save)

        self.device_udid = '192.168.56.101:5555'
        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.ijinshan.kbatterydoctor',
            'appActivity': '.SplashActivity',
            'udid': '192.168.56.101:5555',
        }

    def kaiStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        ok = self.findElement4Awhile(self.img_ad_kai_flag, self.fp_ad_kai_flag)
        if False == ok:
            self.logger.warning("Do not find kai in batterydoctor, use default kai imgage")
            cmd = "cp %s ./screenshot.png" %(self.cf.get('BatteryDoctor', 'img_kai'))
            self.run_shell(cmd)

        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.cf.get('BatteryDoctor', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        img_color = cv2.imread('screenshot.png')
        img_color[0:ad_size[1], 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

    def bannerStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        ok, tl, br = self.findElementPos4Awhile(self.img_charge, self.fp_charge)
        assert ok, "Do not find charge element in batterydoctor"
        self.clickEliment(self.device_udid, tl[0], tl[1])
        assert self.findElement4Awhile(self.img_ad_banner_flag,
                                       self.fp_ad_banner_flag), 'Do not find banner in batterydoctor'
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.cf.get('BatteryDoctor', 'ad_banner_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_pos = self.parseArrStr(self.cf.get('BatteryDoctor', 'ad_banner_pos'), ',')
        img_color = cv2.imread('screenshot.png')
        img_color[ad_pos[1]:ad_pos[1] + ad_size[1], ad_pos[0]:ad_pos[0] + ad_size[0]] = ad
        cv2.imwrite(self.composite_ads_path, self.setHeader(img_color))

        self.driver.quit()

    #TODO update batteryCheck method to be staticmethod or classmethod
    def batteryCheck(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        ok, tl, br = self.findElementPos4Awhile(self.img_save, self.fp_save)
        if ok:
            self.clickEliment(self.device_udid, tl[0], tl[1])
            sleep(10)

        self.driver.quit()

    def start(self):
            if 'kai' == self.ad_type:
                self.kaiStart()
            if 'banner' == self.ad_type:
                self.bannerStart()
            if 'check' == self.ad_type:
                self.batteryCheck()


if __name__ == '__main__':
    try:
        autoImg = BatteryDoctorAutoImg('11:49', 0.8, 'ads/640x330.jpg', '../ad_area/corner-ad.png',
                               'banner', '4G', u'吉利新帝豪', u'饼子还能这么吃，秒杀鸡蛋灌饼，完爆煎饼果子，做法还超级简单！')
        #autoImg = BatteryDoctorAutoImg(ad_type='check')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
