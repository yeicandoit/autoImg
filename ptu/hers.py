#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class HersAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.logo = logo
        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/hers_H60-L11.conf')

        self.img_ad_feeds_flag = cv2.imread(self.config.get('hers', 'img_ad_feeds_flag'), 0)
        self.fp_ad_feeds_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_feeds_flag)))
        self.img_ad_feeds_split = cv2.imread(self.config.get('hers', 'img_ad_feeds_split'), 0)
        self.fp_ad_feeds_split = str(imagehash.dhash(Image.fromarray(self.img_ad_feeds_split)))
        self.img_feeds_flag = cv2.imread(self.config.get('hers', 'img_feeds_flag'), 0)
        self.fp_feeds_flag = str(imagehash.dhash(Image.fromarray(self.img_feeds_flag)))
        self.img_say = cv2.imread(self.config.get('hers', 'img_say'), 0)
        self.fp_say = str(imagehash.dhash(Image.fromarray(self.img_say)))

        self.logger.debug("fp_ad_feeds_flag:%s, fp_ad_feeds_split:%s, fp_say:%s, fp_feeds_flag:%s", self.fp_ad_feeds_flag,
                          self.fp_ad_feeds_split, self.fp_feeds_flag, self.fp_say)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'cn.j.hers',
            'appActivity': 'cn.j.guang.ui.activity.StartActivity',
            'udid': '192.168.56.101:5555',
        }

    def assembleFeedsAd(self):
        blank_height = self.config.getint('hers', 'ad_feeds_blank_height')
        ad_size = self.parseArrStr(self.config.get('hers', 'ad_feeds_size'), ',')
        word_height = self.config.getint('hers', 'word_height')
        blank = cv2.imread(self.config.get('hers', 'img_ad_feeds_blank'))
        ad_desc_pos = self.parseArrStr(self.config.get('hers', 'desc_pos'), ',')

        doc_1stline_max_len = self.set1stDocLength(self.doc, 'hers', self.config)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            ad_desc_pos[1] += word_height
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # logo
        ad_logo_origin = cv2.imread(self.logo)
        ad_logo_size = self.parseArrStr(self.config.get('hers', 'ad_feeds_logo_size'), ',')
        ad_logo = cv2.resize(ad_logo_origin, (ad_logo_size[0], ad_logo_size[1]))
        cv2.imwrite('tmp_img/ad_logo.png', ad_logo)
        ad_logo = self.circle_corder_image('tmp_img/ad_logo.png', 12)
        ad_logo_pos = self.parseArrStr(self.config.get('hers', 'ad_feeds_logo_pos'), ',')
        ad_feeds_bottom = self.warterMarkPos(cv2.imread(self.config.get('hers', 'img_ad_feeds_bottom')),
                                             cv2.imread(ad_logo, cv2.IMREAD_UNCHANGED), ad_logo_pos,
                                             (ad_logo_pos[0] + ad_logo_size[0], ad_logo_pos[1] + ad_logo_size[1]))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('hers', 'img_ad_feeds_bottom'))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = ad_feeds_bottom

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

        if '' != self.desc:
            ttfont = ImageFont.truetype("font/UbuntuDroid.ttf", self.config.getint('hers', 'desc_size'))
            ad_desc_color = self.parseArrStr(self.config.get('hers', 'desc_color'), ',')
            draw.text((ad_desc_pos[0], ad_desc_pos[1]), self.desc,
                      fill=(ad_desc_color[0], ad_desc_color[1], ad_desc_color[2]), font=ttfont)

        if '' != self.doc:
            ttfont = ImageFont.truetype("font/UbuntuDroid.ttf", self.config.getint('hers', 'doc_size'))
            doc_pos = self.parseArrStr(self.config.get('hers', 'doc_pos'), ',')
            ad_doc_pos = (doc_pos[0], doc_pos[1])
            ad_doc_color = self.parseArrStr(self.config.get('hers', 'doc_color'), ',')
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
        assert self.findElement4Awhile(self.img_say, self.fp_say), "Have not found say in hers app"
        self.driver.swipe(self.screen_width / 2, self.screen_height * 3 / 4,
                          self.screen_width / 2, self.screen_height / 4)
        self.driver.implicitly_wait(10)
        assert self.findElement4Awhile(self.img_feeds_flag, self.fp_feeds_flag), "Have not found feeds news in hers app"

        bottom_height = self.config.getint('hers', 'bottom_height')
        blank_height = self.config.getint('hers', 'ad_feeds_blank_height')
        if len(self.doc) > self.set1stDocLength(self.doc, 'hers', self.config):
            blank_height = blank_height + self.config.getint('hers', 'word_height')

        top_left, bottom_right = self.findFeedsArea(self.img_ad_feeds_split, self.fp_ad_feeds_split,
                                                    self.img_ad_feeds_flag, self.fp_ad_feeds_flag,
                                                    blank_height, bottom_height)

        ad = self.assembleFeedsAd()

        #Ensure ads been loaded
        sleep(3)
        self.driver.get_screenshot_as_file('screenshot.png')
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
        autoImg = HersAutoImg('11:49', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                               u'省钱小助手', u'看，质量非常好，打折超划算，在家穿很好呢我期待', logo='ads/banner640_100.jpg')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
