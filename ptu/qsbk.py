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

        if "feeds" == self.ad_type:
            self.logo = logo
            self.img_split = cv2.imread(self.config.get('qsbk', 'img_feeds_split'), 0)
            self.fp_split = str(imagehash.dhash(Image.fromarray(self.img_split)))
            self.logger.debug("fp_split:%s", self.fp_split)

    def kaiStart(self):
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_w, ad_h = self.parseArrStr(self.config.get('qsbk', 'ad_kai_size'), ',')
        ad = cv2.resize(ad_origin, (ad_w, ad_h))

        #Add corner
        img_skip = self.config.get('qsbk', 'img_skip')
        ad_skip_size = self.getImgWH(img_skip)
        tl = (self.screen_width - ad_skip_size[0], 0)
        br = (self.screen_width, ad_skip_size[1])
        ad = self.warterMarkPos(ad, cv2.imread(img_skip, cv2.IMREAD_UNCHANGED), tl, br)
        img_ad_corner = self.config.get('qsbk', 'img_ad_corner')
        ad_corner_w, ad_corner_h = self.getImgWH(img_ad_corner)
        tl = (self.screen_width - ad_corner_w, ad_h-ad_corner_h)
        br = (self.screen_width, ad_h)
        ad = self.warterMarkPos(ad, cv2.imread(img_ad_corner, cv2.IMREAD_UNCHANGED), tl, br)

        img_color = cv2.imread(self.background)
        img_color[0:ad_h, 0:ad_w] = ad
        cv2.imwrite(self.composite_ads_path, img_color)

    def assembleFeedsAd(self, is_bottom):
        blank_height = self.config.getint('qsbk', 'feeds_blank_height')
        ad_w, ad_h = self.parseArrStr(self.config.get('qsbk', 'feeds_ad_size'), ',')
        word_height = self.config.getint('qsbk', 'word_height')
        blank = cv2.imread(self.config.get('qsbk', 'img_blank'))
        split_w, split_h = self.getImgWH(self.config.get('qsbk', 'img_feeds_split'))

        doc_1stline_max_len = self.set1stDocLength(self.doc, 'qsbk', self.config)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        bkg_no_split_h = blank_height - split_h
        bkg_no_split = cv2.resize(blank, (self.screen_width, bkg_no_split_h))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('qsbk', "img_feeds_bottom"))
        bkg_no_split[bkg_no_split_h - bottom_height:bkg_no_split_h, 0:self.screen_width] \
            = cv2.imread(self.config.get('qsbk', "img_feeds_bottom"))

        # Add logo
        logo_x, logo_y = self.parseArrStr(self.config.get('qsbk', 'feeds_logo_pos'), ',')
        logo_w, logo_h = self.parseArrStr(self.config.get('qsbk', 'feeds_logo_size'), ',')
        mask = cv2.imread(self.circle_image(self.logo), cv2.IMREAD_UNCHANGED)
        mask = cv2.resize(mask, (logo_w, logo_h))
        bkg_no_split = self.warterMarkPos(bkg_no_split, mask, (logo_x, logo_y), (logo_x+logo_w, logo_y+logo_h));

        # Add ad
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_w, ad_h))
        ad_y = bkg_no_split_h - bottom_height - ad_h
        ad_x = (self.screen_width - ad_w - 2) / 2
        bkg_no_split[ad_y:ad_y+ad_h, ad_x:ad_x+ad_w] = ad
        cv2.imwrite('tmp_img/tmp.png', bkg_no_split)

        # Print doc and desc in the bkg
        font = self.config.get('qsbk', 'font')
        doc_size = self.config.getint('qsbk', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('qsbk', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('qsbk', 'doc_pos'), ',')
        doc_1stline_max_len = self.set1stDocLength(self.doc, 'qsbk', self.config)
        desc_size = self.config.getint('qsbk', 'desc_size')
        desc_color = self.parseArrStr(self.config.get('qsbk', 'desc_color'), ',')
        desc_pos = self.parseArrStr(self.config.get('qsbk', 'desc_pos'), ',')

        bkg_no_split =  self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height, self.desc, desc_size, desc_color, desc_pos)
        if is_bottom:
            bkg[blank_height-split_h:blank_height, 0:self.screen_width] = \
                cv2.imread(self.config.get('qsbk', 'img_feeds_split'))
            bkg[0:bkg_no_split_h, 0:self.screen_width] = bkg_no_split
        else:
            bkg[0:split_h, 0:self.screen_width] = cv2.imread(self.config.get('qsbk', 'img_feeds_split'))
            bkg[split_h:blank_height, 0:self.screen_width] = bkg_no_split

        return bkg

    def feedsStart(self):
        blank_height = self.config.getint('qsbk', 'feeds_blank_height')
        if len(self.doc) > self.set1stDocLength(self.doc, 'qsbk', self.config):
            blank_height += self.config.getint('qsbk', 'word_height')
        bottom_height = self.config.getint('qsbk', 'feeds_bottom_height')
        header_height = self.config.getint('qsbk', 'feeds_header_height')
        # is_bottome indicate insert ad after split or before
        is_bottom = True
        # The ad area should be >= the biggest feeds ad height(its doc is two line) and app bottom
        try:
            top_left, bottom_right = self.findFeedsAreaInBg(self.background, self.img_split, self.fp_split,
                                                            blank_height,
                                                            bottom_height, is_bottom)
        except:
            is_bottom = False
            top_left, bottom_right = self.findFeedsAreaInBg(self.background, self.img_split, self.fp_split,
                                                            blank_height,
                                                            header_height, is_bottom)
        ad = self.assembleFeedsAd(is_bottom)

        img_color = cv2.imread(self.background)
        if is_bottom:
            bottom_y = self.screen_height - bottom_height
            ad_bottom_height = bottom_y - bottom_right[1] - blank_height
            img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
                img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
            img_color[bottom_right[1]:bottom_right[1] + blank_height, 0:self.screen_width] = ad
        else:
            ad_header_height = top_left[1] - header_height - blank_height
            img_color[header_height:header_height+ad_header_height, 0:self.screen_width] = \
                img_color[top_left[1]-ad_header_height:top_left[1], 0:self.screen_width]
            img_color[top_left[1]-blank_height:top_left[1], 0:self.screen_width] = ad

        img_header_path = self.cf.get('header', 'img_header')
        ok, img_color = self.updateHeader(img_color, img_header_path, self.time, self.battery, self.network,
                                          self.cf, 'header')

        cv2.imwrite(self.composite_ads_path, img_color)

    def start(self):
            if 'kai' == self.ad_type:
                self.kaiStart()
            if 'feeds' == self.ad_type:
                self.feedsStart()



if __name__ == '__main__':
    try:
        autoImg = QSBKAutoImgBg('11:49', 0.8, 'ads/browser_ad.jpg', '../ad_area/corner-ad.png', 'kai', '4G',
                               u'花一样的钱，做不一样的家...', u'房市有变，在上海月入1W的可以考虑买房了！',
                                 logo='ads/qsbk/logo.jpg', background='ads/qsbk/IMG_0065.PNG')
        #autoImg = QSBKAutoImgBg('11:49', 0.8, 'ads/browser_ad.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
        #                        u'苏宁易购', u'别瞎买了，到苏宁换购一台全新苹果花不到3500！',
        #                        logo='ads/qsbk/logo.jpg', background='ads/qsbk/IMG_0064.PNG')

        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
