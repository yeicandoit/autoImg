#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import traceback
import random
import ConfigParser
from base import Base

class EsbookAutoImg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = ''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/esbook_H8.conf')

        self.img_insert_good_flag = cv2.imread(self.config.get('esbook', 'img_insert_good_flag'), 0)
        self.fp_insert_good_flag = str(imagehash.dhash(Image.fromarray(self.img_insert_good_flag)))
        self.img_insert_read_flag = cv2.imread(self.config.get('esbook', 'img_insert_read_flag'), 0)
        self.fp_insert_read_flag = str(imagehash.dhash(Image.fromarray(self.img_insert_read_flag)))
        self.img_insert_battery = cv2.imread(self.config.get('esbook', 'img_insert_battery'), 0)
        self.fp_insert_battery = str(imagehash.dhash(Image.fromarray(self.img_insert_battery)))
        self.logger.debug("fp_insert_good_flag:%s, fp_insert_read_flag:%s, fp_insert_battery:%s",
                          self.fp_insert_good_flag, self.fp_insert_read_flag, self.fp_insert_battery)

        self.device_udid = 'WTK7N16923009805'
        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.esbook.reader',
            'appActivity': '.activity.ActLoading',
            'udid': 'WTK7N16923009805',
        }

    def bottom(self, img, time, battery):
        """set time and network. Time looks like 14:01. network is 3G, 4G and wifi"""
        if len(time) < 5:
            return False, None
        if battery > self.cf.getfloat('battery', 'capacity_max') or battery < self.cf.getfloat('battery', 'capacity_min'):
            return  False, None

        #img = cv2.imread(self.config.get("esbook", "bottom"))
        # battery capacity position in battery
        #bc_top_left = (self.config.getint('esbook', 'capacity_top_left_x'), self.config.getint('esbook', 'capacity_top_left_y'))
        battery_pos = self.parseArrStr(self.config.get('esbook', 'battery_pos'), ',')
        capacity_pos = self.parseArrStr(self.config.get('esbook', 'capacity_pos'), ',')

        # Set battery
        capacity_width, capacity_height = self.getImgWH(self.config.get('esbook', 'capacity'))
        capacity_setting_width = int(capacity_width * battery)
        img_capacity = cv2.imread(self.config.get("esbook", 'capacity'))
        img_bc = cv2.resize(img_capacity, (capacity_setting_width, capacity_height))
        img[capacity_pos[1]:capacity_pos[1] + capacity_height, capacity_pos[0]:capacity_pos[0] + capacity_setting_width] = img_bc
        img_capacity_head = cv2.imread(self.config.get("esbook", "capacity_head"))
        capacity_head_x = capacity_pos[0] + capacity_setting_width
        capacity_head_width, _ = self.getImgWH(self.config.get("esbook", "capacity_head"))
        img[capacity_pos[1]:capacity_pos[1] + capacity_height, capacity_head_x:capacity_head_x + capacity_head_width] = img_capacity_head

        # Set time
        num_size = self.parseArrStr(self.config.get('esbook', 'num_size'), ',')
        IMG_NUM_WIDTH = num_size[0]
        IMG_NUM_HEIGHT = num_size[1]
        num_pos = self.parseArrStr(self.config.get('esbook', 'num_pos'), ',')
        IMG_COLON_WIDTH = self.config.getint('esbook', 'colon_width')
        num_pos = self.parseArrStr(self.config.get('esbook', 'num_pos'), ',')
        NUM_TOP_LEFT_WIDTH = num_pos[0]
        NUM_TOP_LEFT_HEIGHT = num_pos[1]

        h = NUM_TOP_LEFT_HEIGHT
        h1 = NUM_TOP_LEFT_HEIGHT + IMG_NUM_HEIGHT
        w = NUM_TOP_LEFT_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.config.get("esbook", time[0]))
        w = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.config.get("esbook", time[1]))
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.config.get("esbook", 'colon'))
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.config.get("esbook", time[3]))
        w = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 4 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.config.get("esbook", time[4]))

        return True, img


    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        sleep(8)

        ok, tl, br = self.findElementPos4Awhile(self.img_insert_good_flag, self.fp_insert_good_flag)
        assert ok, "Do not find jingxuan option in esbook"
        self.clickEliment(self.device_udid, tl[0], tl[1])

        randS = random.randint(1, 3)
        for _ in range(randS):
            try:
                self.driver.swipe(self.screen_width / 2, self.screen_height * 3 / 4, self.screen_width / 2,
                                  self.screen_height / 4)
                self.driver.implicitly_wait(10)
            except:
                pass
        sleep(3)

        article_area = self.parseArrStr(self.config.get('esbook', 'article_area'), ',')
        random_y = random.randint(article_area[0], article_area[1])
        self.clickEliment(self.device_udid, self.screen_width/2, random_y)
        ok, tl, br = self.findElementPos4Awhile(self.img_insert_read_flag, self.fp_insert_read_flag)
        assert ok, "Do not find read button in esbook"
        self.clickEliment(self.device_udid, tl[0], tl[1])
        assert self.findElement4Awhile(self.img_insert_battery, self.fp_insert_battery), "Article is not shown in esbook"
        randS = random.randint(3, 15)
        article_click_point = self.parseArrStr(self.config.get('esbook', 'article_click_point'), ',')
        for _ in range(randS):
            self.clickEliment(self.device_udid, article_click_point[0], article_click_point[1])
            #sleep(0.2)
        self.driver.get_screenshot_as_file('screenshot.png')

        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get('esbook', 'ad_insert_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_corner_origin = cv2.imread(self.config.get('esbook', 'img_ad_corner'), cv2.IMREAD_UNCHANGED)
        ad_corner_size = self.parseArrStr(self.config.get('esbook', 'ad_insert_cornser_size'), ',')
        ad_corner = cv2.resize(ad_corner_origin, (ad_corner_size[0], ad_corner_size[1]))
        cv2.imwrite('tmp_img/tmp.png', ad_corner)
        cv2.imwrite('tmp_img/tmp_ad.png', ad)
        ad = self.warterMark('tmp_img/tmp_ad.png', 'tmp_img/tmp.png')


        ad_pos = self.parseArrStr(self.config.get('esbook', 'ad_insert_pos'), ',')
        img_color = cv2.imread('screenshot.png')
        img_color[ad_pos[1]:ad_pos[1]+ad_size[1], ad_pos[0]:ad_pos[0]+ad_size[0]] = ad
        ok, img_color_bottom = self.bottom(img_color, self.time, self.battery)
        if ok:
            img_color = img_color_bottom
        cv2.imwrite(self.composite_ads_path, img_color)

        self.driver.quit()

class EsbookAutoImgBg(Base):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo = '', background=''):
        Base.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf='conf/iphone6.conf', background=background)

        self.config = ConfigParser.ConfigParser()
        self.config.read('/Users/iclick/wangqiang/autoImg/conf/esbook_iphone6.conf')

    def start(self):
        ad_origin = cv2.imread(self.img_paste_ad)
        ad_size = self.parseArrStr(self.config.get('esbook', 'ad_insert_size'), ',')
        ad = cv2.resize(ad_origin, (ad_size[0], ad_size[1]))
        ad_corner_origin = cv2.imread(self.config.get('esbook', 'img_ad_corner'), cv2.IMREAD_UNCHANGED)
        #ad_corner_size = self.parseArrStr(self.config.get('esbook', 'ad_insert_cornser_size'), ',')
        #ad_corner = cv2.resize(ad_corner_origin, (ad_corner_size[0], ad_corner_size[1]))
        #cv2.imwrite('tmp_img/tmp.png', ad_corner)
        #cv2.imwrite('tmp_img/tmp_ad.png', ad)
        #ad = self.warterMark('tmp_img/tmp_ad.png', 'tmp_img/tmp.png')


        ad_pos = self.parseArrStr(self.config.get('esbook', 'ad_insert_pos'), ',')
        img_color = cv2.imread(self.background)
        img_color[ad_pos[1]:ad_pos[1]+ad_size[1], ad_pos[0]:ad_pos[0]+ad_size[0]] = ad
        ok, img_set_time = self.setTime(img_color, self.time, self.config, 'esbook')
        if ok:
            img_color = img_set_time
        ok, img_set_battery = self.setBattery(img_color, self.battery, self.config, 'esbook')
        cv2.imwrite(self.composite_ads_path, img_color)

if __name__ == '__main__':
    try:
        #autoImg = EsbookAutoImg('09:55', 0.8, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
        #                       u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100', logo='ads/logo.jpg')
        autoImg = EsbookAutoImgBg('09:55', 0.2, 'ads/feeds1000x560.jpg', '../ad_area/corner-ad.png', 'feeds', '4G',
                                u'吉利新帝豪', u'狂欢11.11跨品牌满减，流行尖货满199-100',
                                  logo='ads/logo.jpg', background='ads/esbook/IMG_0086.PNG')
        autoImg.compositeImage()
    except Exception as e:
        traceback.print_exc()
