#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image
import random
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class QnewsAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, ad_type, network, desc, doc, save_path)

        self.config = ConfigParser.ConfigParser()
        self.config.read('conf/qnews_H60-L11.conf')

        if 'feeds_banner' != self.ad_type:
            self.img_split = cv2.imread(self.config.get('Qnews', 'img_split'), 0)
        else:
            self.img_split = cv2.imread(self.config.get('Qnews', 'img_banner_split'), 0)
            self.img_comment = cv2.imread(self.config.get('Qnews', 'img_comment'), 0)
            self.fp_comment = str(imagehash.dhash(Image.fromarray(self.img_comment)))
            self.img_comment_one = cv2.imread(self.config.get('Qnews', 'img_comment_one'), 0)
            self.fp_comment_one = str(imagehash.dhash(Image.fromarray(self.img_comment_one)))
            self.img_comment_one_ = cv2.imread(self.config.get('Qnews', 'img_comment_one_'), 0)
            self.fp_comment_one_ = str(imagehash.dhash(Image.fromarray(self.img_comment_one_)))

            self.logger.debug("fp_comment:%s, fp_comment_one:%s, fp_comment_one_:%s", self.fp_comment, self.fp_comment_one,
                         self.fp_comment_one_)

        self.fp_split = str(imagehash.dhash(Image.fromarray(self.img_split)))
        self.img_ad_flag = cv2.imread(self.config.get('Qnews', 'img_ad_flag'), 0)
        self.fp_ad_flag = str(imagehash.dhash(Image.fromarray(self.img_ad_flag)))
        self.logger.debug("fp_split:%s, fp_ad_flag:%s", self.fp_split, self.fp_ad_flag)

        self.device_udid = '192.168.56.101:5555'

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.tencent.news',
            'appActivity': '.activity.SplashActivity',
            'udid': '192.168.56.101:5555',
        }

    def assembleFeedsBigAd(self):
        blank_height = self.config.getint('Qnews', 'feeds_big_blank_height')
        ad_width, ad_height = self.parseArrStr(self.config.get('Qnews', 'feeds_big_ad_size'), ',')
        word_height = self.config.getint('Qnews', 'word_height')
        blank = cv2.imread(self.config.get('Qnews', 'img_blank'))
        font = self.config.get('Qnews', 'font')
        doc_size = self.config.getint('Qnews', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('Qnews', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_big_doc_pos'), ',')

        check_pos = (self.screen_width + ad_width) / 2
        doc_1stline_max_len = self.find1stDoclen(font, self.doc, doc_size, (doc_pos[0], 0), check_pos)

        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('Qnews', 'img_ad_area_bottom'))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('Qnews', 'img_ad_area_bottom'))

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_width, ad_height))
        ad_top_y = blank_height - bottom_height - ad_height
        ad_left_x = (self.screen_width - ad_width) / 2
        bkg[ad_top_y:ad_top_y + ad_height, ad_left_x:ad_left_x + ad_width] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height), blank_height

    def assembleFeedsSmallAd(self):
        blank_height = self.config.getint('Qnews', 'feeds_small_blank_height')
        ad_width, ad_height = self.parseArrStr(self.config.get('Qnews', 'feeds_small_ad_size'), ',')
        word_height = self.config.getint('Qnews', 'word_height')
        blank = cv2.imread(self.config.get('Qnews', 'img_blank'))
        ad_left_x, ad_top_y = self.parseArrStr(self.config.get('Qnews', 'feeds_small_ad_pos'), ',')
        font = self.config.get('Qnews', 'font')
        doc_size = self.config.getint('Qnews', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('Qnews', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_big_doc_pos'), ',')

        check_pos = self.config.getint('Qnews', 'feeds_small_doc_1stline_check_x')
        doc_1stline_max_len = self.find1stDoclen(font, self.doc, doc_size, (doc_pos[0], 0), check_pos)

        # set ad backgroud
        bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('Qnews', 'img_feeds_small_bottom'))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('Qnews', 'img_feeds_small_bottom'))

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_width, ad_height))
        bkg[ad_top_y:ad_top_y + ad_height, ad_left_x:ad_left_x + ad_width] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height), blank_height

    def assembleFeedsMultiAd(self):
        blank_height = self.config.getint('Qnews', 'feeds_multi_blank_height')
        ad_width = self.config.getint('Qnews', 'feeds_multi_ad_width')
        one_ad_width = self.config.getint('Qnews', 'feeds_multi_1_ad_width')
        ad_height = self.config.getint('Qnews', 'feeds_multi_ad_height')
        word_height = self.config.getint('Qnews', 'word_height')
        blank = cv2.imread(self.config.get('Qnews', 'img_blank'))
        font = self.config.get('Qnews', 'font')
        doc_size = self.config.getint('Qnews', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('Qnews', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_multi_doc_pos'), ',')

        check_pos = (self.screen_width + ad_width) / 2
        doc_1stline_max_len = self.find1stDoclen(font, self.doc, doc_size, (doc_pos[0], 0), check_pos)

        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('Qnews', 'img_ad_area_bottom'))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('Qnews', 'img_ad_area_bottom'))

        # Add ad
        img_ads = self.img_paste_ad.split(',')
        assert len(img_ads) == 3, "Should have 3 ad images for feeds_multi"
        ad_top_y = blank_height - bottom_height - ad_height
        ad_left_x = (self.screen_width - ad_width) / 2
        ad_space_between = (ad_width - 3 * one_ad_width) / 2
        bkg[ad_top_y:ad_top_y + ad_height, ad_left_x:ad_left_x + one_ad_width] \
            = cv2.resize(cv2.imread(img_ads[0]), (one_ad_width, ad_height))
        bkg[ad_top_y:ad_top_y + ad_height,
        ad_left_x + one_ad_width + ad_space_between:ad_left_x + 2 * one_ad_width + ad_space_between] \
            = cv2.resize(cv2.imread(img_ads[1]), (one_ad_width, ad_height))
        bkg[ad_top_y:ad_top_y + ad_height,
        ad_left_x + 2 * one_ad_width + 2 * ad_space_between:ad_left_x + 3 * one_ad_width + 2 * ad_space_between] \
            = cv2.resize(cv2.imread(img_ads[2]), (one_ad_width, ad_height))
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height), blank_height

    def assembleFeedsAd(self):
        if "feeds_big" == self.ad_type:
            ad, bh = self.assembleFeedsBigAd()
        elif "feeds_small" == self.ad_type:
            ad, bh = self.assembleFeedsSmallAd()
        elif "feeds_multi" == self.ad_type:
            ad, bh = self.assembleFeedsMultiAd()
        else:
            ad = None
            bh = 0
        return ad, bh

    def feedsStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(10)

        randS = random.randint(1, 3)
        for _ in range(randS):
            try:
                self.driver.swipe(self.screen_width / 2, self.screen_height / 4, self.screen_width / 2,
                                  self.screen_height * 3 / 4)
                self.driver.implicitly_wait(10)
            except:
                pass
        sleep(3)

        ad, blank_height = self.assembleFeedsAd()
        bottom_height = self.config.getint('Qnews', 'bottom_height')
        # The ad area should be >= the biggest feeds ad height(its doc is two line) and app bottom
        top_left, bottom_right = self.findFeedsArea(self.img_split, self.fp_split, self.img_ad_flag, self.fp_ad_flag,
                                                    blank_height, bottom_height)
        self.driver.get_screenshot_as_file('screenshot.png')

        img_color = cv2.imread('screenshot.png')
        bottom_y = self.cf.getint('screen', 'height') - bottom_height
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[bottom_right[1]:bottom_right[1] + blank_height, 0:self.screen_width] = ad

        # Add header image
        ok, img_header = self.header(self.time, self.battery, self.network)
        if ok:
            img_color[0:self.ad_header_height, 0:self.ad_header_width] = img_header

        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

    def bannerStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(10)

        # refresh news
        try:
            self.driver.swipe(self.screen_width / 2, self.screen_height / 4, self.screen_width / 2,
                              self.screen_height * 3 / 4)
            self.driver.implicitly_wait(10)
        except:
            pass
        sleep(3)

        cnt = 0
        while 1:
            cnt += 1
            assert cnt != 3, "Have not found news with comment in qnew"
            try:
                self.driver.swipe(self.screen_width / 2, self.screen_height * 3 / 4, self.screen_width / 2,
                                  self.screen_height / 4)
                self.driver.implicitly_wait(10)
            except:
                pass
            self.driver.get_screenshot_as_file('screenshot.png')
            ok, top_left, bottom_right = self.findMatchedArea(cv2.imread('screenshot.png', 0), self.img_comment,
                                                              self.fp_comment)
            if ok:
                cmd = "adb -s %s shell input tap %d %d" % (self.device_udid, top_left[0], top_left[1])
                self.run_shell(cmd)
                sleep(3)
                break

        self.driver.get_screenshot_as_file('screenshot.png')
        ok, _, _ = self.findMatchedArea(cv2.imread('screenshot.png', 0), self.img_comment_one,
                                        self.fp_comment_one)
        if ok != True:
            ok, _, _ = self.findMatchedArea(cv2.imread('screenshot.png', 0), self.img_comment_one_,
                                            self.fp_comment_one_)
        assert ok, 'Do not find comment in qnew'
        pos = self.parseArrStr(self.config.get('Qnews', 'comment_pos'), ',')
        cmd = "adb -s %s shell input tap %d %d" % (self.device_udid, pos[0], pos[1])
        self.run_shell(cmd)
        sleep(3)

        _, blank_height = self.getImgWH(self.config.get('Qnews', 'img_banner_area'))
        bottom_height = self.config.getint('Qnews', 'bottom_height')
        top_left, bottom_right = self.findFeedsArea(self.img_split, self.fp_split, self.img_ad_flag, self.fp_ad_flag,
                                                    blank_height, bottom_height)
        self.driver.get_screenshot_as_file('screenshot.png')
        ad_w, ad_h = self.parseArrStr(self.config.get('Qnews', 'feeds_banner_size'), ',')
        img_ad = cv2.resize(cv2.imread(self.img_paste_ad), (ad_w, ad_h))
        ad_x, ad_y = self.parseArrStr(self.config.get('Qnews', 'feeds_banner_pos'), ',')
        ad = cv2.imread(self.config.get('Qnews', 'img_banner_area'))
        ad[ad_y:ad_y + ad_h, ad_x:ad_x + ad_w] = img_ad

        img_color = cv2.imread('screenshot.png')
        bottom_y = self.cf.getint('screen', 'height') - bottom_height
        ad_bottom_height = bottom_y - top_left[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[top_left[1]:top_left[1] + blank_height, 0:self.screen_width] = ad

        # Add header image
        ok, img_header = self.header(self.time, self.battery, self.network)
        if ok:
            img_color[0:self.ad_header_height, 0:self.ad_header_width] = img_header

        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

    def start(self):
        if 'feeds_banner' != self.ad_type:
            self.feedsStart()
        else:
            self.bannerStart()


class QnewsAutoImgBg(Base):
    def __init__(self, params):
        Base.__init__(self, params['time'], params['battery'], params['adImg'], params['adType'], params['network'],
                      params['title'], params['doc'], params['savePath'], params['conf'], params['basemap'])

        self.config = ConfigParser.ConfigParser()
        self.config.read(params['config'])
        if 'feeds_banner' != self.ad_type:
            self.img_split = cv2.imread(self.config.get('Qnews', 'img_feeds_split'), 0)
        else:
            self.img_split = cv2.imread(self.config.get('Qnews', 'img_banner_split'), 0)

        self.fp_split = str(imagehash.dhash(Image.fromarray(self.img_split)))
        self.logger.debug("fp_split:%s", self.fp_split)

        if '10' == params['adCornerType']:
            self.ad_area_bottom = 'img_' + self.ad_type + '_area_bottom'
        elif '11' == params['adCornerType']:
            self.ad_area_bottom = 'img_' + self.ad_type + '_area_bottom_1'

    def assembleFeedsBigAd(self):
        blank_height = self.config.getint('Qnews', 'feeds_big_blank_height')
        ad_size = self.parseArrStr(self.config.get('Qnews', 'feeds_big_ad_size'), ',')
        word_height = self.config.getint('Qnews', 'word_height')
        blank = cv2.imread(self.config.get('Qnews', 'img_blank'))

        doc_1stline_max_len = self.set1stDocLength(self.doc, 'Qnews',self.config)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('Qnews', self.ad_area_bottom))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('Qnews', self.ad_area_bottom))

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_size[0], ad_size[1]))
        ad_top_y = blank_height - bottom_height - ad_size[1]
        ad_left_x = (self.screen_width - ad_size[0]) / 2
        bkg[ad_top_y:ad_top_y + ad_size[1], ad_left_x:ad_left_x + ad_size[0]] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        font = self.config.get('Qnews', 'font')
        doc_size = self.config.getint('Qnews', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('Qnews', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_big_doc_pos'), ',')
        doc_1stline_max_len = self.set1stDocLength(self.doc, 'Qnews', self.config)
        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height)

    def assembleFeedsSmallAd(self):
        blank_height = self.config.getint('Qnews', 'feeds_small_blank_height')
        ad_size = self.parseArrStr(self.config.get('Qnews', 'feeds_small_ad_size'), ',')
        ad_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_small_ad_pos'), ',')
        word_height = self.config.getint('Qnews', 'word_height')
        blank = cv2.imread(self.config.get('Qnews', 'img_blank'))

        bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('Qnews', self.ad_area_bottom))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('Qnews', self.ad_area_bottom))

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_size[0], ad_size[1]))
        bkg[ad_pos[1]:ad_pos[1] + ad_size[1], ad_pos[0]:ad_pos[0] + ad_size[0]] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        font = self.config.get('Qnews', 'font')
        doc_size = self.config.getint('Qnews', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('Qnews', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_small_doc_pos'), ',')
        doc_1stline_max_len = self.set1stDocLength(self.doc, 'Qnews', self.config, d1len='feeds_small_doc_1stline_px_len')
        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height)

    def assembleFeedsMultiAd(self):
        blank_height = self.config.getint('Qnews', 'feeds_multi_blank_height')
        ad_size = self.parseArrStr(self.config.get('Qnews', 'feeds_multi_ad_size'), ',')
        multi_ad_width = self.config.getint('Qnews', 'feeds_multi_ad_width')
        word_height = self.config.getint('Qnews', 'word_height')
        blank = cv2.imread(self.config.get('Qnews', 'img_blank'))

        doc_1stline_max_len = self.set1stDocLength(self.doc, 'Qnews', self.config)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('Qnews', self.ad_area_bottom))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('Qnews', self.ad_area_bottom))

        # Add ad
        img_ads = self.img_paste_ad.split(',')
        assert len(img_ads) == 3, "Should have 3 ad images for feeds_multi"
        ad_top_y = blank_height - bottom_height - ad_size[1]
        ad_left_x = (self.screen_width - multi_ad_width) / 2
        ad_space_between = (multi_ad_width - 3 * ad_size[0]) / 2
        for i in range(0, len(img_ads)):
            bkg[ad_top_y:ad_top_y + ad_size[1], ad_left_x:ad_left_x + ad_size[0]] \
                = cv2.resize(cv2.imread(img_ads[i]), (ad_size[0], ad_size[1]))
            ad_left_x += ad_size[0]+ad_space_between
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        font = self.config.get('Qnews', 'font')
        doc_size = self.config.getint('Qnews', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('Qnews', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('Qnews', 'feeds_multi_doc_pos'), ',')
        doc_1stline_max_len = self.set1stDocLength(self.doc, 'Qnews', self.config)
        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height)

    def assembleFeedsAd(self):
        if "feeds_big" == self.ad_type:
            ad = self.assembleFeedsBigAd()
        elif "feeds_small" == self.ad_type:
            ad = self.assembleFeedsSmallAd()
        elif "feeds_multi" == self.ad_type:
            ad = self.assembleFeedsMultiAd()
        else:
            ad = None
        return ad


    def getFeedsBlankHeight(self):
        key = self.ad_type + "_blank_height"
        blank_height = self.config.getint('Qnews', key)
        if len(self.doc) > self.set1stDocLength(self.doc, 'Qnews', self.config) and "feeds_small" != self.ad_type:
            blank_height = blank_height + self.config.getint('Qnews', 'word_height')

        return blank_height


    def feedsStart(self):
        blank_height = self.getFeedsBlankHeight()
        bottom_height = self.config.getint('Qnews', 'feeds_bottom_height')
        # The ad area should be >= the biggest feeds ad height(its doc is two line) and app bottom
        top_left, bottom_right = self.findFeedsAreaInBg(self.background, self.img_split, self.fp_split, blank_height,
                                                        bottom_height)
        ad = self.assembleFeedsAd()

        img_color = cv2.imread(self.background)
        bottom_y = self.screen_height - bottom_height
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[bottom_right[1]:bottom_right[1] + blank_height, 0:self.screen_width] = ad

        #Add header image
        ok, img_color = self.updateHeader(img_color, "", self.time, self.battery, self.network, self.config, 'header')

        cv2.imwrite(self.composite_ads_path, img_color)

    def bannerStart(self):
        _, blank_height = self.getImgWH(self.config.get('Qnews', 'img_banner_area'))
        bottom_height = self.config.getint('Qnews', 'banner_bottom_height')
        top_left, bottom_right = self.findFeedsAreaInBg(self.background, self.img_split, self.fp_split, blank_height,
                                                        bottom_height)
        ad_w, ad_h = self.parseArrStr(self.config.get('Qnews', 'banner_ad_size'), ',')
        img_ad = cv2.resize(cv2.imread(self.img_paste_ad), (ad_w, ad_h))
        ad_x, ad_y = self.parseArrStr(self.config.get('Qnews', 'banner_ad_pos'), ',')
        ad = cv2.imread(self.config.get('Qnews', 'img_banner_area'))
        ad[ad_y:ad_y + ad_h, ad_x:ad_x + ad_w] = img_ad

        img_color = cv2.imread(self.background)
        bottom_y = self.screen_height - bottom_height
        ad_bottom_height = bottom_y - top_left[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[top_left[1]:top_left[1] + blank_height, 0:self.screen_width] = ad

        # Add header image
        _, img_color = self.updateHeader(img_color, "", self.time, self.battery, self.network, self.config, 'header')
        cv2.imwrite(self.composite_ads_path, img_color)

    def start(self):
        if 'feeds_banner' != self.ad_type:
            self.feedsStart()
        else:
            self.bannerStart()


if __name__ == '__main__':
    try:
        #autoImg = QnewsAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg', '10', 'feeds_big', '4G',
        #                       u'吉利新帝豪', u'17岁被TVB力捧红，两段恋情一段婚姻皆失败，儿子成骄傲', logo='ads/logo.jpg',
        #                        u'吉利新帝豪', u'长城守护我们，我们守护长城', logo='ads/logo.jpg',
        #                        u'吉利新帝豪', u'她和胡歌分手，却因为粘孙红雷爆红，如今身价千万豪车出行！', logo='ads/logo.jpg',
        #                         background = 'ads/qnews_bg.png')
        #autoImg = QnewsAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg,ads/feeds1000x560.jpg,ads/feeds1000x560.jpg', '10', 'feeds_multi', '4G',
        #                         u'吉利新帝豪', u'专业管道疏通，半小时到达', logo='ads/logo.jpg', background='ads/qnews_bg.png')
        #autoImg = QnewsAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg',
        #                         '10', 'feeds_small', '4G',
        #                         u'吉利新帝豪', u'奥迪Q5这个外观有看头还降价达19.85万', logo='ads/logo.jpg',
        #                         background='ads/qnews_bg.png')
        #autoImg = QnewsAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg',
        #                         '10', 'feeds_banner', '4G',
        #                         u'吉利新帝豪', u'用身份证号就能查出个人信用，你查了吗？', logo='ads/logo.jpg',
        #                         background='ads/qnew_banner_bg.jpg')
        autoImg = QnewsAutoImg('11:49', 0.8, 'ads/640x330.jpg', 'ad_area/corner-ad.png',
                               'feeds_banner', '4G', u'吉利新帝豪', u'饼子还能这么吃，秒杀鸡蛋灌饼，完爆煎饼果子，做法还超级简单！')
        #autoImg = QnewsAutoImg('11:49', 0.8, 'ads/230x160.jpg,ads/230x160.jpg,ads/230x160.jpg', 'ad_area/corner-ad.png',
        #                       'feeds_multi', '4G', u'吉利新帝豪', u'上海浦东即将举办大型家具展，入场门票免费领')


        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
