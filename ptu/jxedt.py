#coding=utf-8
from appium import webdriver
from PIL import Image
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class JxedtAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, ad_type, network, desc,
                         doc, save_path)
        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/jxedt_H60-L11.conf')

        self.section = 'jxedt'
        self.img_banner_flag = cv2.imread(self.config.get(self.section, 'img_banner_flag'), 0)
        self.fp_banner_flag = str(imagehash.dhash(Image.fromarray(self.img_banner_flag)))
        self.img_banner_flag_2 = cv2.imread(self.config.get(self.section, 'img_banner_flag_2'), 0)
        self.fp_banner_flag_2 = str(imagehash.dhash(Image.fromarray(self.img_banner_flag_2)))

        self.logger.debug("fp_banner_flag:%s, fp_banner_flag_2:%s", self.fp_banner_flag, self.fp_banner_flag_2)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.jxedt',
            'appActivity': '.ui.activitys.GuideActivity',
            'udid': '192.168.56.101:5555',
        }
        self.device_udid = "192.168.56.101:5555"

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)

        ok, tl, br = self.findElementPos4Awhile(self.img_banner_flag, self.fp_banner_flag)
        assert ok, 'Do not find banner flag 1'
        self.clickEliment(self.device_udid, tl[0], tl[1])
        assert self.findElement4Awhile(self.img_banner_flag_2, self.fp_banner_flag_2), 'Do not find banner area'

        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get(self.section, 'ad_banner_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_corner_w, ad_corner_h = self.getImgWH(self.config.get(self.section, 'img_corner_1'))
        ad_corner = cv2.imread(self.config.get(self.section, 'img_corner_1'), cv2.IMREAD_UNCHANGED)
        ad = self.warterMarkPos(ad, ad_corner, (self.screen_width-ad_corner_w, 0), (self.screen_width, ad_corner_h))
        ad_corner_2_size = self.getImgWH(self.config.get(self.section, 'img_corner_2'))
        ad_corner_2 = cv2.imread(self.config.get(self.section, 'img_corner_2'), cv2.IMREAD_UNCHANGED)
        ad = self.warterMarkPos(ad, ad_corner_2, (0,0), ad_corner_2_size)
        ad_pos_x, ad_pos_y = self.parseArrStr(self.config.get(self.section, 'ad_banner_pos'), ',')
        img_color = cv2.imread('screenshot.png')
        img_color[ad_pos_y:ad_pos_y+ad_size[1], ad_pos_x:ad_pos_x+ad_size[0]] = ad
        cv2.imwrite(self.composite_ads_path, self.setHeader(img_color))

        self.driver.quit()


if __name__ == '__main__':
    try:
        autoImg = JxedtAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100', logo='ads/logo.jpg')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
