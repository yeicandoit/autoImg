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
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        if 'feeds' == self.ad_type:
            self.logo = logo
            self.img_ad_feeds_flag = cv2.imread(self.cf.get('Wantu', 'img_ad_feeds_flag'), 0)
            self.fp_ad_feeds_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_feeds_flag)))
            self.logger.debug("fp_ad_feeds_flag:%s", self.fp_ad_feeds_flag)

        if 'kai' == self.ad_type:
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

    def kaiStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        assert self.findElement4Awhile(self.img_ad_kai_flag, self.fp_ad_kai_flag, 20), "Do not find kai ad in wantu"
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.cf.get('Wantu', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        img_color = cv2.imread('screenshot.png')
        img_color[0:ad_size[1], 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

    def assembleFeedsAd(self):
        ad_area = cv2.imread(self.cf.get('Wantu', 'img_ad_feeds_area'))
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.cf.get('Wantu', 'ad_feeds_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_logo_origin = cv2.imread(self.logo)
        ad_logo_size = self.parseArrStr(self.cf.get('Wantu', 'ad_feeds_logo_size'), ',')
        ad_logo = cv2.resize(ad_logo_origin, (ad_logo_size[0], ad_logo_size[1]))
        cv2.imwrite('tmp_img/ad_logo.png', ad_logo)
        ad_logo = self.circle_image('tmp_img/ad_logo.png')
        ad_area[0:ad_size[1], 0:ad_size[0]] = ad

        # water mark detail and logo into ad_area
        ad_logo_pos = self.parseArrStr(self.cf.get('Wantu', 'ad_feeds_logo_pos'), ',')
        ad_area = self.warterMarkPos(ad_area, cv2.imread(ad_logo, cv2.IMREAD_UNCHANGED), ad_logo_pos,
                                     (ad_logo_pos[0] + ad_logo_size[0], ad_logo_pos[1] + ad_logo_size[1]))
        ad_detail_pos = self.parseArrStr(self.cf.get('Wantu', 'ad_feeds_detail_pos'), ',')
        ad_detail_length, ad_detail_height = self.getImgWH(self.cf.get('Wantu', 'img_ad_feeds_detail'))
        ad_area = self.warterMarkPos(ad_area,
                                     cv2.imread(self.cf.get('Wantu', 'img_ad_feeds_detail'), cv2.IMREAD_UNCHANGED),
                                     ad_detail_pos,
                                     (ad_detail_pos[0] + ad_detail_length, ad_detail_pos[1] + ad_detail_height))
        cv2.imwrite('tmp_img/tmp.png', ad_area)

        # Print doc and desc in the bkg
        im = Image.open('tmp_img/tmp.png')
        draw = ImageDraw.Draw(im)
        if '' != self.doc:
            doc_1stline_max_len = self.set1stDocLen(self.doc, 'Wantu')
            ttfont = ImageFont.truetype("font/UbuntuDroid.ttf", self.cf.getint('Wantu', 'doc_size'))
            ad_doc_pos = self.parseArrStr(self.cf.get('Wantu', 'doc_pos'), ',')
            ad_doc_color = self.parseArrStr(self.cf.get('Wantu', 'doc_color'), ',')
            if len(self.doc) <= doc_1stline_max_len:
                draw.text(ad_doc_pos, self.doc, fill=(ad_doc_color[0], ad_doc_color[1], ad_doc_color[2]), font=ttfont)
            else:
                ad_doc_pos1 = (ad_doc_pos[0], ad_doc_pos[1] + self.cf.getint('Wantu', 'word_height'))
                draw.text(ad_doc_pos, self.doc[:doc_1stline_max_len],
                          fill=(ad_doc_color[0], ad_doc_color[1], ad_doc_color[2]),
                          font=ttfont)
                draw.text(ad_doc_pos1, self.doc[doc_1stline_max_len:],
                          fill=(ad_doc_color[0], ad_doc_color[1], ad_doc_color[2]),
                          font=ttfont)

        im.save('tmp_img/tmp.png')
        return cv2.imread('tmp_img/tmp.png')

    def feedsStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(3)

        assert self.findElement4Awhile(self.img_ad_feeds_flag, self.fp_ad_feeds_flag, 20), "Do not find feeds ad in wantu"

        img_color = cv2.imread('screenshot.png')
        ad_area_pos = self.parseArrStr(self.cf.get('Wantu', 'ad_area_pos'), ',')
        ad_area_size = self.getImgWH(self.cf.get('Wantu', 'img_ad_feeds_area'))
        img_color[ad_area_pos[1]:ad_area_pos[1]+ad_area_size[1], ad_area_pos[0]:ad_area_pos[0]+ad_area_size[0]] \
            = self.assembleFeedsAd()

        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

    def start(self):
            if 'kai' == self.ad_type:
                self.kaiStart()
            if 'feeds' == self.ad_type:
                self.feedsStart()


if __name__ == '__main__':
    try:
        autoImg = WantuAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100', logo='ads/logo.jpg')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
