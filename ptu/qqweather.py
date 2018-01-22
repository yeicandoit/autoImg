#coding=utf-8
from PIL import Image
import cv2
import imagehash
import traceback
import ConfigParser
from base import Base

class QQWeatherBg(Base):
    def __init__(self, params):
        Base.__init__(self, params['time'], params['battery'], params['adImg'], params['adType'], params['network'],
                      params['title'], params['doc'], params['savePath'], params['conf'], params['basemap'])

        self.config = ConfigParser.ConfigParser()
        self.config.read(params['config'])

        self.img_corner_mark = self.config.get('qqweather', 'img_corner_mark')
        self.img_now = cv2.imread(self.config.get('qqweather', 'img_now'), 0)
        self.fp_now = str(imagehash.dhash(Image.fromarray(self.img_now)))
        self.logger.debug("fp_now:%s", self.fp_now)

    def start(self):
        ad_width, ad_height = self.parseArrStr(self.config.get('qqweather', 'ad_size'), ',')
        img_now2ad_distance = self.config.getint('qqweather', 'img_now2ad_distance')
        ok, tl, br = self.findMatchedArea(cv2.imread(self.background, 0), self.img_now, self.fp_now)
        assert ok, "Do not find now in weather ad background"
        assert br[1]+img_now2ad_distance+ad_height < self.screen_height, "Could not insert ad in weather ad background"

        ad = cv2.resize(cv2.imread(self.img_paste_ad), (ad_width, ad_height))
        ad_corner_x, ad_corner_y = self.parseArrStr(self.config.get('qqweather', 'ad_corner_pos'), ',')
        ad_corner_width, ad_corner_height = self.getImgWH(self.img_corner_mark)
        ad = self.warterMarkPos(ad, cv2.imread(self.img_corner_mark, cv2.IMREAD_UNCHANGED), (ad_corner_x, ad_corner_y),
                                (ad_corner_x+ad_corner_width, ad_corner_y+ad_corner_height))
        ad_top_left_x = self.config.getint('qqweather', 'ad_top_left_x')
        ad_top_left_y = br[1] + img_now2ad_distance
        img_color = cv2.imread(self.background)
        img_color[ad_top_left_y:ad_top_left_y+ad_height, ad_top_left_x:ad_top_left_x + ad_width] = ad

        img_header_path = self.cf.get('header', 'img_header')
        _, img_color = self.updateHeader(img_color, img_header_path, self.time, self.battery, self.network, self.cf,
                                         'header')
        cv2.imwrite(self.composite_ads_path, img_color)

if __name__ == '__main__':
    try:
        #autoImg = WechatAutoImgBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/corner-mark.png', 'fine_big', '4G',
        #                          background='ads/wechat_bg/IMG_0036.png')
        autoImg = QQWeatherBg('09:46', 0.9, 'ads/feeds1000x560.jpg', 'ad_area/qweather/iphone6/corner-mark.png', 'image_text', '4G',
                                  u'用最少的成本', u'投放适合本地商户的朋友圈本地推广广告', background='ads/qqweather_bg/qqweather.png')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
