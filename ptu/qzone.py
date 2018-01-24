#coding=utf-8
from PIL import Image
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class QzoneBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo='', background='',
                 stars=0.0):
        Base.__init__(self, time, battery, img_paste_ad, ad_type, network, desc,
                         doc, save_path, conf='conf/iphone6.conf', background=background)
        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/qzone_iphone6.conf')

        self.stars = stars
        self.logo = logo
        self.img_split = cv2.imread(self.config.get('qzone', 'img_feeds_split'), 0)
        self.fp_split = str(imagehash.dhash(Image.fromarray(self.img_split)))
        self.logger.debug("fp_split:%s", self.fp_split)

    def assembleFeedsAd(self):
        blank_height = self.config.getint('qzone', 'feeds_blank_height')
        ad_w, ad_h = self.parseArrStr(self.config.get('qzone', 'feeds_ad_size'), ',')
        word_height = self.config.getint('qzone', 'word_height')
        blank = cv2.imread(self.config.get('qzone', 'img_blank'))
        font = self.config.get('qzone', 'font')
        doc_size = self.config.getint('qzone', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('qzone', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('qzone', 'doc_pos'), ',')
        desc_size = self.config.getint('qzone', 'desc_size')
        desc_color = self.parseArrStr(self.config.get('qzone', 'desc_color'), ',')
        desc_pos = self.parseArrStr(self.config.get('qzone', 'desc_pos'), ',')

        check_pos = (self.screen_width + ad_w) / 2
        doc_1stline_max_len = self.find1stDoclen(font, self.doc, doc_size, (doc_pos[0], 0), check_pos)
        # set ad backgroud
        if len(self.doc) <= doc_1stline_max_len:
            bkg = cv2.resize(blank, (self.screen_width, blank_height))
        else:
            blank_height = blank_height + word_height
            bkg = cv2.resize(blank, (self.screen_width, blank_height))

        # Add bottom
        _, bottom_height = self.getImgWH(self.config.get('qzone', "img_ad_area_bottom"))
        bkg[blank_height - bottom_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.config.get('qzone', "img_ad_area_bottom"))

        # Add ad flag
        ad_flag_w, ad_flag_h = self.getImgWH(self.config.get('qzone', 'img_ad_flag'))
        bkg[0:ad_flag_h, 0:ad_flag_w] = cv2.imread(self.config.get('qzone', 'img_ad_flag'))

        # Add logo
        logo_x, logo_y = self.parseArrStr(self.config.get('qzone', 'feeds_logo_pos'), ',')
        logo_w, logo_h = self.parseArrStr(self.config.get('qzone', 'feeds_logo_size'), ',')
        mask = cv2.imread(self.circle_image(self.logo), cv2.IMREAD_UNCHANGED)
        mask = cv2.resize(mask, (logo_w, logo_h))
        bkg = self.warterMarkPos(bkg, mask, (logo_x, logo_y), (logo_x+logo_w, logo_y+logo_h));

        # Add ad
        ad_bg = cv2.imread(self.config.get('qzone', 'img_ad_bg'))
        ad_bg[1:ad_h+1, 1:ad_w+1] = cv2.resize(cv2.imread(self.img_paste_ad), (ad_w, ad_h))
        cv2.imwrite("tmp_img/qzone_ad.png", ad_bg)
        ad_bg_path = self.circle_corder_image("tmp_img/qzone_ad.png", 8, (1, 0, 1, 0))
        ad_bg_y = blank_height - bottom_height - ad_h - 1
        ad_bg_x = (self.screen_width - ad_w - 2) / 2
        bkg = self.warterMarkPos(bkg, cv2.imread(ad_bg_path, cv2.IMREAD_UNCHANGED), (ad_bg_x, ad_bg_y),
                                 (ad_bg_x+ad_w+2, ad_bg_y+ad_h+1))
        cv2.imwrite('tmp_img/tmp.png', bkg)

        # Print doc and desc in the bkg
        ad_assemble = self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height, self.desc, desc_size, desc_color, desc_pos)

        return ad_assemble, blank_height

    def start(self):
        ad, blank_height = self.assembleFeedsAd()
        bottom_height = self.config.getint('qzone', 'feeds_bottom_height')
        # The ad area should be >= the biggest feeds ad height(its doc is two line) and app bottom
        top_left, bottom_right = self.findFeedsAreaInBg(self.background, self.img_split, self.fp_split, blank_height,
                                                        bottom_height)

        img_color = cv2.imread(self.background)
        bottom_y = self.screen_height - bottom_height
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img_color[bottom_y - ad_bottom_height: bottom_y, 0:self.screen_width] = \
            img_color[bottom_right[1]:bottom_right[1] + ad_bottom_height, 0:self.screen_width]
        img_color[bottom_right[1]:bottom_right[1] + blank_height, 0:self.screen_width] = ad

        # Do not set header because the header of qzone is translucent
        #img_header_path = self.config.get('header', 'img_header')
        #ok, img_color = self.updateHeader(img_color, img_header_path, self.time, self.battery, self.network, self.config, 'header')

        cv2.imwrite(self.composite_ads_path, img_color)


if __name__ == '__main__':
    try:
        #autoImg = QQBrowserBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png', 'image_text', '4G',
        #                          u'用最少的成本', u'重点中学女学生操场生产，老师看到刚苏醒的女孩，捂脸大哭直喊：可惜了', background='ads/qzone_bg/IMG_0004.PNG')

        autoImg = QzoneBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png',
                              'image_text', '4G', u'大秦王朝', u'回到战国当主公，85万大军已集结，你能主宰大秦??**，统一六国吗？!!?',
                                background='ads/qzone_bg/bg.PNG', stars=2.0, logo='ads/insert-600_500.jpg')

        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
