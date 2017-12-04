#coding=utf-8
from PIL import Image
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class WechatAutoImgBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo='', background=''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/iphone6.conf', background=background)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/wechat_iphone6.conf')

        self.img_top = cv2.imread(self.config.get('wechat', 'img_top'), 0)
        self.img_tousu = cv2.imread(self.config.get('wechat', 'img_tousu'), 0)
        self.img_good_message = cv2.imread(self.cf.get('image_path', 'good_message'), 0)
        self.img_write_message = cv2.imread(self.cf.get('image_path', 'write_message'), 0)
        self.fp_tousu = str(imagehash.dhash(Image.fromarray(self.img_tousu)))
        self.fp_good_message = str(imagehash.dhash(Image.fromarray(self.img_good_message)))
        self.fp_write_message = str(imagehash.dhash(Image.fromarray(self.img_write_message)))
        self.logger.debug("fp_tousu:%s, fp_good_message:%s, fp_write_message:%s", self.fp_tousu, self.fp_good_message,
                          self.fp_write_message)
        if "image_text" != self.ad_type:
            self.img_ad_message = self.config.get('wechat', 'img_ad_message')
        else:
            self.img_ad_message = self.config.get('wechat', 'img_ad_message_image_text')
        self.ad_width, self.ad_height = self.parseArrStr(self.config.get('wechat', self.ad_type+'_size'), ',')

        self.NONE = 0
        self.GOOD_MESSAGE = 1
        self.WRITE_MESSAGE = 2

    def findTousu(self, img):
        """ Find the tousu position """
        crop, top_left, bottom_right = self.findMatched(img, self.img_tousu)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        self.logger.debug("Found img_tousu_message hash is:" + fp)
        is_top = self.hammingDistOK(fp, self.fp_tousu)
        return is_top, top_left, bottom_right

    def findAdAreaBottom(self, img):
        """Find good_message or write_message position"""
        crop, top_left, bottom_right = self.findMatched(img, self.img_good_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        self.logger.debug("Found img_good_message hash is:" + fp)
        if self.hammingDistOK(fp, self.fp_good_message, 5):
            return self.GOOD_MESSAGE, top_left, bottom_right
        crop, top_left, bottom_right = self.findMatched(img, self.img_write_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        self.logger.debug("Found img_write_message hash is:" + fp)
        if self.hammingDistOK(fp, self.fp_write_message):
            return self.WRITE_MESSAGE, top_left, bottom_right
        return self.NONE, top_left, bottom_right


    def findAdArea(self, img_bg):
        """We assume that ad area is less than half screen, then we have following logic"""
        img = cv2.imread(img_bg, 0)
        ok, top_left, bottom_right = self.findTousu(img)
        assert ok, "Do not find wechat account aticle ad tousu flag"
        #Find good_mesage or write_message
        type, top_left1, bottom_right1 = self.findAdAreaBottom(img)

        cv2.rectangle(img, (0, bottom_right[1]), (bottom_right1[0], top_left1[1]), (0, 0, 0), 1)
        cv2.imwrite('tmp_img/debug_wechat_account.png', img)
        return type, (0, bottom_right[1]), (bottom_right1[0], top_left1[1])

    def imageText(self):
        ad_bg = cv2.imread(self.config.get('wechat', 'img_image_text_bg'))
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_width, ad_height = self.parseArrStr(self.config.get('wechat', 'image_text_ad_size'), ',')
        ad = cv2.resize(ad_origin, (ad_width, ad_height))
        ad_x, ad_y = self.parseArrStr(self.config.get('wechat', 'image_text_ad_pos'), ',')
        ad_bg[ad_y:ad_y+ad_height, ad_x:ad_x+ad_width] = ad

        # Ad corner mark
        ad_bg_w, ad_bg_h = self.parseArrStr(self.config.get("wechat", 'image_text_size'), ',')
        corner_w, corner_h = self.getImgWH(self.img_corner_mark)
        corner_tl = (ad_bg_w-2-corner_w, ad_bg_h-2-corner_h)
        corner_br = (ad_bg_w-2, ad_bg_h-2)
        ad_bg = self.warterMarkPos(ad_bg, cv2.imread(self.img_corner_mark, cv2.IMREAD_UNCHANGED), corner_tl, corner_br)
        cv2.imwrite('tmp_img/tuwen.png', ad_bg)

        # Print doc and desc in the bkg
        font = self.config.get('wechat', 'font')
        doc_size = self.config.getint('wechat', 'image_text_doc_size')
        doc_color = self.parseArrStr(self.config.get('wechat', 'image_text_doc_color'), ',')
        doc_pos = self.parseArrStr(self.config.get('wechat', 'image_text_doc_pos'), ',')
        doc_1stline_max_len = self.set1stDocLength(self.doc, 'wechat', self.config)
        word_height = self.config.getint('wechat', 'image_text_word_height')
        desc_size = self.config.getint('wechat', 'image_text_desc_size')
        desc_color = self.parseArrStr(self.config.get('wechat', 'image_text_desc_color'), ',')
        desc_pos = self.parseArrStr(self.config.get('wechat', 'image_text_desc_pos'), ',')
        return self.drawText('tmp_img/tuwen.png', font, self.doc, doc_size, doc_color, doc_pos, doc_1stline_max_len,
                             word_height, self.desc, desc_size, desc_color, desc_pos)

    def start(self):
        ad_bottom_type, left, right = self.findAdArea(self.background)
        self.logger.debug("bottom type:%d", ad_bottom_type)

        img_color = cv2.imread(self.background)
        # Compare ad area and area we need
        area_height = right[1] - left[1]
        img_gray = cv2.imread(self.background, 0)
        _, h_ad_message = self.getImgWH(self.img_ad_message)
        wanted_height = self.ad_height + h_ad_message
        if ad_bottom_type == self.GOOD_MESSAGE:
            wanted_height += self.config.getint('wechat', 'distance_good_message')
        elif ad_bottom_type == self.WRITE_MESSAGE:
            wanted_height += self.config.getint('wechat', 'distance_write_message')
        elif self.NONE == ad_bottom_type:
            wanted_height += self.config.getint('wechat', 'distance_bottom')

        # ad area is bigger than wanted, should shrink
        # ad area is bigger than wanted, but there is no message block, paste ad directly
        if_ad_bottom = if_ad_above = False
        if area_height - wanted_height > 3 and self.NONE != ad_bottom_type:
            self.logger.debug("Should shrink ad area")
            assert 0, "ad area height:%s is bigger than wanted height:%s, should shrink. But do not support this " \
                      "situation now" %(area_height, wanted_height)

        # ad area is smaller than wanted, should enlarge
        if area_height - wanted_height < -3:
            self.logger.debug("Should enlarge ad area")
            if self.screen_height / 2 <= left[1]:
                if_ad_above = True
                # Calculate ad top area
                crop, img_top_left, img_top_right = self.findMatched(img_gray, self.img_top)
                ad_above = img_color[img_top_right[1] + wanted_height - area_height:left[1], 0:self.screen_width]
                # update ad area
                left = (0, left[1] + area_height - wanted_height)
            else:
                if_ad_bottom = True
                ad_bottom = img_color[right[1]:self.screen_height + area_height - wanted_height, 0:self.screen_width]
                right = (self.screen_width, right[1] + wanted_height - area_height)

        # if ad area size changed, set area ad above
        if if_ad_above:
            img_color[img_top_right[1]:left[1], 0:self.screen_width] = ad_above
        elif if_ad_bottom:
            img_color[right[1]:self.screen_height, 0:self.screen_width] = ad_bottom

        # Paint ad area to be blank
        img_blank = cv2.imread(self.config.get('wechat', 'img_blank'))
        img_blank_resize = cv2.resize(img_blank, (self.screen_width, right[1] - left[1]))
        img_color[left[1]:right[1], 0:self.screen_width] = img_blank_resize
        # Paint img_ad_message
        img_color[left[1]:left[1] + h_ad_message, 0:self.screen_width] = cv2.imread(self.img_ad_message)

        # Add our ad image
        # if 'banner' == self.ad_type:
        #    img_ad = self.warterMark(self.img_paste_ad, self.img_corner_mark)
        #    img_ad_resize = cv2.resize(img_ad, (self.ad_width, self.ad_height))
        if 'banner' == self.ad_type or 'fine_big' == self.ad_type:
            img_ad_resize = cv2.resize(cv2.imread(self.img_paste_ad), (self.ad_width, self.ad_height))
            cv2.imwrite('tmp_img/wechat.png', img_ad_resize)
            # img_corner_resize = cv2.resize(cv2.imread(self.img_corner_mark, cv2.IMREAD_UNCHANGED),
            #                               (self.cf.getint('fine_big', 'corner_width'), self.cf.getint('fine_big', 'corner_height')))
            # cv2.imwrite('tmp_img/fine_big_corner.png', img_corner_resize)
            img_ad_resize = self.warterMark('tmp_img/wechat.png', self.img_corner_mark)
        elif 'image_text' == self.ad_type:
            img_ad_resize = self.imageText()
        left_side = (self.screen_width - self.ad_width) / 2
        img_color[left[1] + h_ad_message:left[1] + h_ad_message + self.ad_height,
        left_side:left_side + self.ad_width] = img_ad_resize

        # Add header image
        img_header_path = self.config.get('header', 'img_header')
        _, img_color = self.updateHeader(img_color, img_header_path, self.time, self.battery, self.network, self.config, 'header')
        cv2.imwrite(self.composite_ads_path, img_color)


if __name__ == '__main__':
    try:
        #autoImg = WechatAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/corner-mark.png', 'fine_big', '4G',
        #                          background='ads/wechat_bg/IMG_0036.png')
        autoImg = WechatAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/corner-mark.png', 'image_text', '4G',
                                  u'用最少的成本', u'投放适合本地商户的朋友圈本地推广广告', background='ads/wechat_bg/wechat_image_text.png')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
