#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class QSBKAutoImgBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo='', background=''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/iphone6.conf', background=background)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/qsbk_iphone6.conf')

    def kaiStart(self):
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_w, ad_h = self.parseArrStr(self.config.get('qsbk', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_w, ad_h))

        #Add corner
        #ad_kai_corner_1 = self.config.get('Wantu', 'img_ad_kai_corner_1')
        #ad_kai_corner_2 = self.config.get('Wantu', 'img_ad_kai_corner_2')
        #ad_kai_corner_3 = self.config.get('Wantu', 'img_ad_kai_corner_3')
        #ad_kai_corner_1_size = self.getImgWH(ad_kai_corner_1)
        #ad_kai_corner_2_size = self.getImgWH(ad_kai_corner_2)
        #ad_kai_corner_3_size = self.getImgWH(ad_kai_corner_3)
        #tr2 = (ad_w - ad_kai_corner_2_size[0], ad_h - ad_kai_corner_2_size[1])
        #tr3 = (ad_w - ad_kai_corner_3_size[0], 0)
        #br3 = (ad_w, ad_kai_corner_3_size[1])
        #ad = self.warterMarkPos(ad, cv2.imread(ad_kai_corner_1, cv2.IMREAD_UNCHANGED), (0, 0), ad_kai_corner_1_size)
        #ad = self.warterMarkPos(ad, cv2.imread(ad_kai_corner_2, cv2.IMREAD_UNCHANGED), tr2, (ad_w, ad_h))
        #ad = self.warterMarkPos(ad, cv2.imread(ad_kai_corner_3, cv2.IMREAD_UNCHANGED), tr3, br3)

        img_color = cv2.imread(self.background)
        img_color[0:ad_h, 0:ad_w] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

    def feedsStart(self):
        pass

    def start(self):
            if 'kai' == self.ad_type:
                self.kaiStart()
            if 'feeds' == self.ad_type:
                self.feedsStart()



if __name__ == '__main__':
    try:
        autoImg = QSBKAutoImgBg('11:49', 0.8, 'ads/browser_ad.jpg', '../ad_area/corner-ad.png', 'kai', '4G',
                               u'入冬成功！赶紧做个水润...', u'资生堂明星洗护终结秋冬干燥，给你飘逸秀发、水润弹肌！',
                                 logo='ads/logo.jpg', background='ads/qsbk_bg/IMG_0065.PNG')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
