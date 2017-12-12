#coding=utf-8
from PIL import Image
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class QQBrowserBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo='', background=''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/iphone6.conf', background=background)
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

        doc_1stline_max_len = self.set1stDocLength(self.doc, 'qqbrowser', self.config)
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
        font = self.config.get('qqbrowser', 'font')
        doc_size = self.config.getint('qqbrowser', 'doc_size')
        doc_color = self.parseArrStr(self.config.get('qqbrowser', 'doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('qqbrowser', 'doc_pos'), ',')
        doc_1stline_max_len = self.set1stDocLength(self.doc, 'qqbrowser', self.config)
        desc_size = self.config.getint('qqbrowser', 'desc_size')
        desc_color = self.parseArrStr(self.config.get('qqbrowser', 'desc_color'), ',')

        return self.drawText('tmp_img/tmp.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height, self.desc, desc_size, desc_color, desc_pos)

    def start(self):
        blank_height = self.config.getint('qqbrowser', 'feeds_blank_height')
        if len(self.doc) > self.set1stDocLength(self.doc, 'qqbrowser', self.config):
            blank_height += self.config.getint('qqbrowser', 'word_height')
        bottom_height = self.config.getint('qqbrowser', 'feeds_bottom_height')
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

        # Add header image
        img_header_path = self.config.get('header', 'img_header')
        ok, img_color = self.updateHeader(img_color, img_header_path, self.time, self.battery, self.network, self.config, 'header')

        cv2.imwrite(self.composite_ads_path, img_color)


if __name__ == '__main__':
    try:
        #autoImg = QQBrowserBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png', 'image_text', '4G',
        #                          u'用最少的成本', u'重点中学女学生操场生产，老师看到刚苏醒的女孩，捂脸大哭直喊：可惜了', background='ads/qqbrowser_bg/IMG_0004.PNG')

        autoImg = QQBrowserBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png',
                              'image_text', '4G',
                              u'用最少的成本', u'赵丽颖最美的六个角色，陆贞第6，花千骨第2，第1美的太离谱！', background='ads/qqbrowser_bg/IMG_0004.PNG')

        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
