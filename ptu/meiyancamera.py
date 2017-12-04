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
                         doc, doc1st_line, save_path)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/meiyancamera_H60-L11.conf')

        self.img_ad_kai_flag = cv2.imread(self.config.get('meiyancamera', 'img_ad_kai_flag'), 0)
        self.fp_ad_kai_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_kai_flag)))
        self.logger.debug("fp_ad_kai_flag:%s", self.fp_ad_kai_flag)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.meitu.meiyancamera',
            'appActivity': '.MyxjActivity',
            'udid': '192.168.56.101:5555',
        }

    def assembleFeedsAd(self):
        pass

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        ok = self.findElement4Awhile(self.img_ad_kai_flag, self.fp_ad_kai_flag)
        if False == ok:
            self.logger.warning("Do not find kai in meiyancamera, use default kai imgage")
            cmd = "cp %s ./screenshot.png" % (self.config.get('meiyancamera', 'img_kai'))
            self.run_shell(cmd)

        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get('meiyancamera', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        img_color = cv2.imread('screenshot.png')
        img_color[0:ad_size[1], 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()


if __name__ == '__main__':
    try:
        autoImg = MeiyancameraAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100', logo='ads/logo.jpg')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()