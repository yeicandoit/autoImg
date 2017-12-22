#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class MeiyancameraAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/Honor8.conf')

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/meiyancamera_Honor8.conf')

        self.img_ad_kai_flag = cv2.imread(self.config.get('meiyancamera', 'img_ad_kai_flag'), 0)
        self.fp_ad_kai_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_kai_flag)))
        self.logger.debug("fp_ad_kai_flag:%s", self.fp_ad_kai_flag)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '7.0',
            'deviceName': 'Honor8',
            'appPackage': 'com.meitu.meiyancamera',
            'appActivity': '.MyxjActivity',
            'udid': 'WTK7N16923009805',
        }

    def assembleFeedsAd(self):
        pass

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)

        ok = self.findElement4Awhile(self.img_ad_kai_flag, self.fp_ad_kai_flag)
        if False == ok:
            self.logger.warning("Do not find kai in meiyancamera, use default kai imgage")
            cmd = "cp %s ./screenshot.png" % (self.config.get('meiyancamera', 'img_kai'))
            self.run_shell(cmd)

        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get('meiyancamera', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_corner_w, ad_corner_h = self.getImgWH(self.config.get('meiyancamera', 'img_ad_kai_corner'))
        ad_corner = cv2.imread(self.config.get('meiyancamera', 'img_ad_kai_corner'), cv2.IMREAD_UNCHANGED)
        ad = self.warterMarkPos(ad, ad_corner, (self.screen_width-ad_corner_w, 0), (self.screen_width, ad_corner_h))
        img_color = cv2.imread('screenshot.png')
        img_color[0:ad_size[1], 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

class MeiyancameraAutoImgBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = '', background=''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/iphone6.conf', background=background)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/meiyancamera_iphone6.conf')

    def assembleFeedsAd(self):
        pass

    def start(self):
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get('meiyancamera', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        img_ad_kai_corner = self.config.get('meiyancamera', 'img_ad_kai_corner')
        ad_corner_size = self.getImgWH(img_ad_kai_corner)
        tl = (self.screen_width-ad_corner_size[0], 0)
        br = (self.screen_width, ad_corner_size[1])
        ad = self.warterMarkPos(ad, cv2.imread(img_ad_kai_corner, cv2.IMREAD_UNCHANGED), tl, br)
        img_color = cv2.imread(self.background)
        img_color[0:ad_size[1], 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

if __name__ == '__main__':
    try:
        autoImg = MeiyancameraAutoImgBg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100',
                               logo='ads/logo.jpg', background='ads/meiyancamera/IMG_0078.PNG')
        autoImg = MeiyancameraAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds',
                                        '4G',
                                        u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100',
                                        logo='ads/logo.jpg')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
