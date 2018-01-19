#coding=utf-8
from PIL import Image
from appium import webdriver
import cv2
import imagehash
import traceback
import ConfigParser
import random
from time import sleep
from base import Base

class QQBrowserAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', conf='conf/Honor8.conf'):
        Base.__init__(self, time, battery, img_paste_ad, ad_type, network, desc,
                         doc, save_path, conf)

        self.ad_flag = cv2.imread(self.cf.get('image_path', 'browser_ad'), 0)
        self.fp_ad_flag = str(imagehash.dhash(Image.fromarray(self.ad_flag)))
        self.hot_header = cv2.imread(self.cf.get('image_path', 'browser_hot_header'), 0)
        self.fp_hot_header = str(imagehash.dhash(Image.fromarray(self.hot_header)))
        self.split = cv2.imread(self.cf.get('image_path', 'browser_split'), 0)
        self.fp_split = str(imagehash.dhash(Image.fromarray(self.split)))
        self.img_unfinished_big = cv2.imread(self.cf.get('QQBrowser', 'img_unfinished_big'), 0)
        self.fp_unfinished_big = str(imagehash.dhash(Image.fromarray(self.img_unfinished_big)))
        self.img_unfinished_small = cv2.imread(self.cf.get('QQBrowser', 'img_unfinished_small'), 0)
        self.fp_unfinished_small = str(imagehash.dhash(Image.fromarray(self.img_unfinished_small)))
        self.img_unfinished_multi = cv2.imread(self.cf.get('QQBrowser', 'img_unfinished_multi'), 0)
        self.fp_unfinished_multi = str(imagehash.dhash(Image.fromarray(self.img_unfinished_multi)))


        self.logger.debug("fp_ad_flag:%s, fp_hot_header:%s, fp_split:%s, fp_unfinished_big:%s, fp_unfinished_small:%s"
                     "fp_unfinished_multi:%s", self.fp_ad_flag, self.fp_hot_header, self.fp_split,
                     self.fp_unfinished_big, self.fp_unfinished_small, self.fp_unfinished_multi)

        self.ad_desc_pos = (self.cf.getint('QQBrowser', 'desc_x'), self.cf.getint('QQBrowser', 'desc_y'))
        desc_color = self.cf.getint('QQBrowser', 'desc_color')
        self.ad_desc_color = (desc_color, desc_color, desc_color)
        self.ad_doc_pos = (self.cf.getint('QQBrowser', 'doc_x'), self.cf.getint('QQBrowser', 'doc_y'))
        doc_color = self.cf.getint('QQBrowser', 'doc_color')
        self.ad_doc_color = (doc_color, doc_color, doc_color)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '7.0',
            'deviceName': 'Honor8',
            'appPackage': 'com.tencent.mtt',
            'appActivity': '.MainActivity',
            'udid': 'WTK7N16923009805',
        }
    def findAdArea(self, start_width, start_height, end_width, end_height):
        """ We assume that ad area is less than half screen, then we have following logic.
            QQBrowser will not push ad when accessed too much!!! so insert one ad between news area.
        """
        for _ in (0,random.randint(1, 2)):
            self.driver.swipe(start_width, start_height, end_width, end_height)
            self.driver.implicitly_wait(10)
            sleep(1)
        cnt = 0
        while 1:
            cnt = cnt + 1
            assert cnt != 10, "Do not find ad area"
            try:
                self.driver.swipe(start_width, start_height, end_width, end_height)
                self.driver.implicitly_wait(10)
                #Wait pic or video to be loaded
                sleep(3)
                self.driver.get_screenshot_as_file("screenshot.png")
                img = cv2.imread('screenshot.png', 0)

                #If there is some ads has not finished loading, continue
                ok_big, _, _ = self.findMatchedArea(img, self.img_unfinished_big, self.fp_unfinished_big)
                ok_small, _, _ = self.findMatchedArea(img, self.img_unfinished_small, self.fp_unfinished_small)
                ok_multi, _, _ = self.findMatchedArea(img, self.img_unfinished_multi, self.fp_unfinished_multi)
                if ok_big or ok_small or ok_multi:
                    continue

                ok, top_left, bottom_right = self.findMatchedArea(img, self.split, self.fp_split)
                if ok:
                    # Do not insert ad in page which has already had an ad
                    has_ad_flag, _, _ = self.findMatchedArea(img, self.ad_flag, self.fp_ad_flag)
                    if has_ad_flag:
                        continue
                    #TODO When doc line is 2, ad area height will be bigger than blank_height, should consider this
                    if self.cf.getint('QQBrowser', 'bottom_y') - top_left[1] < self.cf.getint('QQBrowser', 'blank_height') \
                            + self.cf.getint('QQBrowser', 'word_height'):
                        continue
                    break
            except Exception as e:
                self.logger.error('expect:' + repr(e))

        return top_left, bottom_right

    def assembleImg(self):
        blank_height = self.cf.getint('QQBrowser', 'blank_height')
        ad_width = self.cf.getint('QQBrowser', 'ad_width')
        ad_height = self.cf.getint('QQBrowser', 'ad_height')
        split_ad_dis = self.cf.getint('QQBrowser', 'split_ad_dis')
        ad_x = (self.screen_width - ad_width) / 2
        word_height = self.cf.getint('QQBrowser', 'word_height')
        ad_area_bottom_height = self.cf.getint('QQBrowser', 'ad_area_bottom_height')
        blank = cv2.imread(self.cf.get('image_path', 'browser_blank'))
        font = "font/HYQiHei-50S.otf"
        doc_size = self.cf.getint('QQBrowser', 'doc_size')
        desc_size = self.cf.getint('QQBrowser', 'desc_size')
        check_pos = (self.screen_width+ad_width) / 2

        doc_1stline_max_len = self.find1stDoclen(font, self.doc, doc_size, (self.ad_doc_pos[0], 0), check_pos)
        # set ad backgroud
        if len(self.doc) > doc_1stline_max_len:
            blank_height = blank_height + word_height
            split_ad_dis += word_height
            self.ad_desc_pos = (self.ad_desc_pos[0], self.ad_desc_pos[1] + word_height)
        bkg = cv2.resize(blank, (self.screen_width, blank_height))
        ad = cv2.imread(self.img_paste_ad)

        paste_ad = cv2.resize(ad, (ad_width, ad_height))
        bkg[split_ad_dis:split_ad_dis+ad_height, ad_x:ad_x+ad_width] = paste_ad

        bkg[blank_height - ad_area_bottom_height:blank_height, 0:self.screen_width] = \
            cv2.imread(self.cf.get('image_path', 'ad_area_bottom'))
        cv2.imwrite('tmp_img/browser.png', bkg)

        # Print doc and desc in the bkg
        ad_assemble = self.drawText('tmp_img/browser.png', font, self.doc, doc_size, self.ad_doc_color, self.ad_doc_pos,
                                    doc_1stline_max_len, word_height, self.desc, desc_size, self.ad_desc_color,
                                    self.ad_desc_pos)

        return ad_assemble, blank_height

    def setBattery(self, img, battery):
        if battery > self.cf.getfloat('battery', 'capacity_max') or battery < self.cf.getfloat('battery', 'capacity_min'):
            return  False, None

        bc_bottom_right = (
        self.cf.getint('battery', 'capacity_bottom_right_x'), self.cf.getint('battery', 'capacity_bottom_right_y'))
        bc_top_left = (
        self.cf.getint('battery', 'capacity_top_left_x'), self.cf.getint('battery', 'capacity_top_left_y'))

        bc_width = bc_bottom_right[0] - bc_top_left[0]
        bc_height = bc_bottom_right[1] - bc_top_left[1]
        bc_setting_width = int(bc_width * battery)
        img_bc = cv2.imread(self.cf.get("image_path", 'battery_capacity'))
        img_bc = cv2.resize(img_bc, (bc_setting_width, bc_height))
        img[bc_top_left[1]:bc_bottom_right[1], bc_top_left[0]:bc_top_left[0] + bc_setting_width] = img_bc

        return img

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_name(u'首页')
        self.driver.implicitly_wait(10)
        # QQBrowser stores last access position(e.g. 看热点), check whether it stays at 看热点 when open it again
        self.driver.get_screenshot_as_file("screenshot.png")
        img = cv2.imread('screenshot.png', 0)
        is_hot_header, _, _ = self.findMatchedArea(img, self.hot_header, self.fp_hot_header)
        if is_hot_header != True:
            self.driver.tap([(self.cf.getint('QQBrowser', 'hot_x'), self.cf.getint('QQBrowser', 'hot_y'))])
            self.driver.implicitly_wait(10)
        sleep(8)
        #refresh to get latest news
        self.driver.swipe(self.screen_width / 2, self.screen_height / 4, self.screen_width / 2,
                        self.screen_height * 3 / 4, 3000)
        sleep(6)
        top_left, bottom_right = self.findAdArea(self.screen_width / 2, self.screen_height * 3 / 4,
                                                 self.screen_width / 2, self.screen_height / 4)

        ad, blank_height = self.assembleImg()
        img = cv2.imread('screenshot.png')
        bottom_y = self.cf.getint('QQBrowser', 'bottom_y')
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img[bottom_y-ad_bottom_height: bottom_y,0:self.screen_width] = \
            img[bottom_right[1]:bottom_right[1]+ad_bottom_height, 0:self.screen_width]
        img[bottom_right[1]:bottom_right[1]+blank_height, 0:self.screen_width] = ad

        #ok, img_header = self.header(self.time, self.battery, self.network)
        #if ok:
        #    img[0:self.ad_header_height, 0:self.ad_header_width] = img_header
        img_header = self.cf.get("image_path", self.network)
        header_w, header_h = self.getImgWH(img_header)
        img[0:header_h, 0:header_w] = cv2.imread(img_header)
        _, img = self.setTime(img, self.time, self.cf, 'header')
        img = self.setBattery(img, self.battery)
        #cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
        cv2.imwrite(self.composite_ads_path, img)
        self.driver.quit()

class QQBrowserBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo='', background=''):
        Base.__init__(self, time, battery, img_paste_ad, ad_type, network, desc,
                         doc, save_path, conf='conf/iphone6.conf', background=background)
        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/qqbrowser_iphone6.conf')

        self.img_split = cv2.imread(self.config.get('qqbrowser', 'img_feeds_split'), 0)
        self.fp_split = str(imagehash.dhash(Image.fromarray(self.img_split)))
        self.logger.debug("fp_split:%s", self.fp_split)

    def assembleFeedsAd(self):
        blank_height = self.config.getint('qqbrowser', 'feeds_blank_height')
        ad_size = self.parseArrStr(self.config.get('qqbrowser', 'feeds_ad_size'), ',')
        word_height = self.config.getint('qqbrowser', 'word_height')
        desc_pos = self.parseArrStr(self.config.get('qqbrowser', 'desc_pos'), ',')
        blank = cv2.imread(self.config.get('qqbrowser', 'img_blank'))
        font = self.config.get('qqbrowser', 'font')
        doc_size = self.config.getint('qqbrowser', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('qqbrowser', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('qqbrowser', 'doc_pos'), ',')
        desc_size = self.config.getint('qqbrowser', 'desc_size')
        desc_color = self.parseArrStr(self.config.get('qqbrowser', 'desc_color'), ',')

        check_pos = (self.screen_width+ad_size[0]) / 2
        doc_1stline_max_len = self.find1stDoclen(font, self.doc, doc_size, (doc_pos[0], 0), check_pos)
        #doc_1stline_max_len = self.set1stDocLength(self.doc, 'qqbrowser', self.config)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            desc_pos[1] += word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('qqbrowser', "img_ad_area_bottom"))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('qqbrowser', "img_ad_area_bottom"))

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_size[0], ad_size[1]))
        ad_top_y = blank_height - bottom_height - ad_size[1]
        ad_left_x = (self.screen_width - ad_size[0]) / 2
        bkg[ad_top_y:ad_top_y + ad_size[1], ad_left_x:ad_left_x + ad_size[0]] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg

        ad_assemble =  self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height, self.desc, desc_size, desc_color, desc_pos)
        return ad_assemble, blank_height

    def start(self):
        ad, blank_height = self.assembleFeedsAd()
        bottom_height = self.config.getint('qqbrowser', 'feeds_bottom_height')
        # The ad area should be >= the biggest feeds ad height(its doc is two line) and app bottom
        top_left, bottom_right = self.findFeedsAreaInBg(self.background, self.img_split, self.fp_split, blank_height,
                                                        bottom_height)
        img_color = cv2.imread(self.background)
        bottom_y = self.screen_height - bottom_height
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[bottom_right[1]:bottom_right[1] + blank_height, 0:self.screen_width] = ad

        # Add header image
        img_header_path = self.config.get('header', 'img_header')
        ok, img_color = self.updateHeader(img_color, img_header_path, self.time, self.battery, self.network, self.config, 'header')

        cv2.imwrite(self.composite_ads_path, img_color)


if __name__ == '__main__':
    try:
        #autoImg = QQBrowserBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png', 'image_text', '4G',
        #                          u'用最少的成本', u'重点中学女学生操场生产，老师看到刚苏醒的女孩，捂脸大哭直喊：可惜了', background='ads/qqbrowser_bg/IMG_0004.PNG')

        #autoImg = QQBrowserBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png',
        #                      'image_text', '4G',
        #                      u'用最少的成本', u'赵丽颖最美的六个角色，陆贞第6，花千骨第2，第1美的太离谱！', background='ads/qqbrowser_bg/IMG_0004.PNG')
        autoImg = QQBrowserAutoImg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png',
                              'image_text', '4G',
                              u'三星手机', u'岁末购机豪礼任性送，与bixby聊天多聊多领福利')

        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
