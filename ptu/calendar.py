#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
import ConfigParser

from base import Base

class CalendarAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/calendar_H60-L11.conf')

        self.img_ad_feeds_flag = cv2.imread(self.config.get('calendar', 'img_ad_feeds_flag'), 0)
        self.fp_ad_feeds_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_feeds_flag)))
        self.img_ad_feeds_split = cv2.imread(self.config.get('calendar', 'img_ad_feeds_split'), 0)
        self.fp_ad_feeds_split = str(imagehash.dhash(Image.fromarray(self.img_ad_feeds_split)))
        self.logger.debug("fp_ad_feeds_flag:%s, fp_ad_feeds_split:%s", self.fp_ad_feeds_flag, self.fp_ad_feeds_split)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.youloft.calendar',
            'appActivity': '.MainActivity',
            'udid': '192.168.56.101:5555',
        }

    def assembleFeedsAd(self):
        blank_height = self.config.getint('calendar', 'ad_feeds_blank_height')
        ad_size = self.parseArrStr(self.config.get('calendar', 'ad_feeds_size'), ',')
        word_height = self.config.getint('calendar', 'word_height')
        blank = cv2.imread(self.config.get('calendar', 'img_ad_feeds_blank'))

        doc_1stline_max_len = self.set1stDocLength(self.doc, 'calendar', self.config)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('calendar', 'img_ad_feeds_bottom'))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('calendar', 'img_ad_feeds_bottom'))

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_size[0], ad_size[1]))
        ad_top_y = blank_height - bottom_height - ad_size[1]
        ad_left_x = (self.screen_width - ad_size[0]) / 2
        bkg[ad_top_y:ad_top_y + ad_size[1], ad_left_x:ad_left_x + ad_size[0]] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        im = Image.open('tmp_img/tmp.png')
        draw = ImageDraw.Draw(im)
        if '' != self.doc:
            ttfont = ImageFont.truetype("font/UbuntuDroid.ttf", self.config.getint('calendar', 'doc_size'))
            doc_pos = self.parseArrStr(self.config.get('calendar', 'doc_pos'), ',')
            ad_doc_pos = (doc_pos[0], doc_pos[1])
            ad_doc_color = self.parseArrStr(self.config.get('calendar', 'doc_color'), ',')
            if len(self.doc) <= doc_1stline_max_len:
                draw.text(ad_doc_pos, self.doc, fill=(ad_doc_color[0], ad_doc_color[1], ad_doc_color[2]), font=ttfont)
            else:
                ad_doc_pos1 = (ad_doc_pos[0], ad_doc_pos[1] + word_height)
                draw.text(ad_doc_pos, self.doc[:doc_1stline_max_len],
                          fill=(ad_doc_color[0], ad_doc_color[1], ad_doc_color[2]),
                          font=ttfont)
                draw.text(ad_doc_pos1, self.doc[doc_1stline_max_len:],
                          fill=(ad_doc_color[0], ad_doc_color[1], ad_doc_color[2]),
                          font=ttfont)

        im.save('tmp_img/tmp.png')
        return cv2.imread('tmp_img/tmp.png')

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(8)

        bottom_height = self.config.getint('calendar', 'bottom_height')
        blank_height = self.config.getint('calendar', 'ad_feeds_blank_height')
        if len(self.doc) > self.set1stDocLength(self.doc, 'calendar', self.config):
            blank_height = blank_height + self.config.getint('calendar', 'word_height')

        try:
            top_left, bottom_right = self.findFeedsArea(self.img_ad_feeds_split, self.fp_ad_feeds_split,
                                                        self.img_ad_feeds_flag, self.fp_ad_feeds_flag,
                                                        blank_height, bottom_height)
        except:
            top_left, bottom_right = self.findFeedsArea(self.img_ad_feeds_split, self.fp_ad_feeds_split,
                                                        self.img_ad_feeds_flag, self.fp_ad_feeds_flag,
                                                        blank_height, bottom_height)

        ad = self.assembleFeedsAd()
        img_color = cv2.imread('screenshot.png')
        bottom_y = self.screen_height - bottom_height
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[bottom_right[1]:bottom_right[1] + blank_height, 0:self.screen_width] = ad
        cv2.imwrite(self.composite_ads_path, self.setHeader(img_color))

        self.driver.quit()


if __name__ == '__main__':
    try:
        autoImg = CalendarAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'吉利新帝豪', u'【今日必读】这4大生肖的女人，赚钱顾家又旺夫，男人娶了就是福！')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
