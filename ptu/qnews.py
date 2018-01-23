#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class QnewsAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.jxedt',
            'appActivity': '.ui.activitys.GuideActivity',
            'udid': '192.168.56.101:5555',
        }

    def assembleFeedsAd(self):
        pass

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(10)


        self.driver.quit()

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
        autoImg = QnewsAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg', '10', 'feeds_big', '4G',
                               u'吉利新帝豪', u'17岁被TVB力捧红，两段恋情一段婚姻皆失败，儿子成骄傲', logo='ads/logo.jpg',
        #                        u'吉利新帝豪', u'长城守护我们，我们守护长城', logo='ads/logo.jpg',
        #                        u'吉利新帝豪', u'她和胡歌分手，却因为粘孙红雷爆红，如今身价千万豪车出行！', logo='ads/logo.jpg',
                                 background = 'ads/qnews_bg.png')
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

        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
