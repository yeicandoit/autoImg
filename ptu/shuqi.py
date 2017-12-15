#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
import random
import ConfigParser
from base import Base

class ShuqiAutoImgBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = '', background=''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/iphone6.conf', background=background)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/shuqi_iphone6.conf')

    def start(self):
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get('shuqi', 'ad_insert_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_corner_origin = cv2.imread(self.config.get('shuqi', 'img_ad_corner'), cv2.IMREAD_UNCHANGED)
        #ad_corner_size = self.parseArrStr(self.config.get('shuqi', 'ad_insert_cornser_size'), ',')
        #ad_corner = cv2.resize(ad_corner_origin, (ad_corner_size[0], ad_corner_size[1]))
        #cv2.imwrite('tmp_img/tmp.png', ad_corner)
        #cv2.imwrite('tmp_img/tmp_ad.png', ad)
        #ad = self.warterMark('tmp_img/tmp_ad.png', 'tmp_img/tmp.png')


        ad_pos = self.parseArrStr(self.config.get('shuqi', 'ad_insert_pos'), ',')
        img_color = cv2.imread(self.background)
        img_color[ad_pos[1]:ad_pos[1]+ad_size[1], ad_pos[0]:ad_pos[0]+ad_size[0]] = ad
        ok, img_set_time = self.setTime(img_color, self.time, self.config, 'shuqi')
        if ok:
            img_color = img_set_time
        ok, img_set_battery = self.setBattery(img_color, self.battery, self.config, 'shuqi')
        cv2.imwrite(self.composite_ads_path, img_color)

if __name__ == '__main__':
    try:
        autoImg = ShuqiAutoImgBg('09:55', 0.2, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                                u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100',
                                  logo='ads/logo.jpg', background='ads/shuqi/IMG_0088.PNG')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
