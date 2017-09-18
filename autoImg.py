#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import numpy as np
import traceback
import ConfigParser
from appium.webdriver.common.touch_action import TouchAction
import random
import logging
import logging.config
logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main.autoImg')

class AutoImg:
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ads/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', conf='conf/H60-L11.conf'):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(conf)
        self.conf = conf

        self.time = time
        self.battery = battery
        self.img_paste_ad = img_paste_ad
        self.img_corner_mark = img_corner_mark
        self.ad_type = ad_type
        self.network = network
        self.desc = desc
        self.doc = doc
        self.doc1st_line = doc1st_line
        logger.debug("Ad demand is time:%s, battery:%f, img_past_ad:%s, img_corner_mark:%s, "
                     "ad_type:%s, network:%s, desc:%s, doc:%s, doc1st_line:%s", self.time, self.battery,
                     self.img_paste_ad, self.img_corner_mark, self.ad_type, self.network,
                     self.desc, self.doc, self.doc1st_line)
        self.composite_ads_path = save_path
        self.ad_area_path = 'ad_area/'

        self.screen_width = self.cf.getint('screen', 'width')
        self.screen_height = self.cf.getint('screen', 'height')
        self.ad_header_width = self.cf.getint('screen', 'header_width')
        self.ad_header_height = self.cf.getint('screen', 'header_height')

        self.driver = None

    def hammingDistOK(self, s1, s2):
        """ If the distance between image is smaller or equal to 3,
            We think the two images are same
            refer to:http://sm4llb0y.blog.163.com/blog/static/1891239720099195041879/
        """
        assert len(s1) == len(s2)
        return sum([ch1 != ch2 for ch1, ch2 in zip(s1, s2)]) <= 3

    def findMatched(self, src, target):
        """ Find the matched image and its position """
        method = eval('cv2.TM_SQDIFF_NORMED')
        res = cv2.matchTemplate(src, target, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = min_loc
        t_w, t_h = target.shape[::-1]
        bottom_right = (top_left[0] + t_w, top_left[1] + t_h)
        logger.debug("Find matched area, top_left[0]:%d, top_left[1]:%d, bottom_right[0]:%d, bottom_right[1]:%d",
                     top_left[0], top_left[1], bottom_right[0], bottom_right[1])
        crop = src[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        return crop, top_left, bottom_right

    def findMatchedArea(self, src, target, fp_target):
        """ Find the matched image and its position, judge whether it is OK """
        crop, top_left, bottom_right = self.findMatched(src, target)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        logger.debug("Found hash is:" + fp)
        is_top = self.hammingDistOK(fp, fp_target)
        return is_top, top_left, bottom_right

    def warterMark(self, ad, corner_mark, pos='bottom_right'):
        """Add corner_mark on right_bottom for ad"""
        img = cv2.imread(ad)
        img_gray = cv2.imread(ad, 0)
        mask = cv2.imread(corner_mark, cv2.IMREAD_UNCHANGED)
        mask_gray = cv2.imread(corner_mark, 0)
        w_mask, h_mask = mask_gray.shape[::-1]
        w_img, h_img = img_gray.shape[::-1]
        if 'top_right' == pos:
            mask_region = img[0:h_mask, w_img - w_mask:w_img]
        else:
            mask_region = img[h_img - h_mask:h_img, w_img - w_mask:w_img]

        alpha_channel = mask[:, :, 3]
        rgb_channels = mask[:, :, :3]
        alpha_factor = alpha_channel[:, :, np.newaxis].astype(np.float32) / 255.0
        alpha_factor = np.concatenate((alpha_factor, alpha_factor, alpha_factor), axis=2)

        front = rgb_channels.astype(np.float32) * alpha_factor
        back = mask_region.astype(np.float32) * (1 - alpha_factor)
        final_img = front + back
        if 'top_right' == pos:
            img[0:h_mask, w_img - w_mask:w_img] = final_img
        else:
            img[h_img - h_mask:h_img, w_img - w_mask:w_img] = final_img

        return img

    def header(self, time, battery, network, image_cf_path='image_path'):
        """set time and network. Time looks like 14:01. network is 3G, 4G and wifi"""
        if len(time) < 5:
            return False, None
        if battery > self.cf.getfloat('battery', 'capacity_max') or battery < self.cf.getfloat('battery', 'capacity_min'):
            return  False, None
        if network != '3G' and network != '4G' and network != 'wifi':
            return False, None

        # Set network
        img = cv2.imread(self.cf.get(image_cf_path, network))

        # battery capacity position in battery
        bc_bottom_right = (self.cf.getint('battery', 'capacity_bottom_right_x'), self.cf.getint('battery', 'capacity_bottom_right_y'))
        bc_top_left = (self.cf.getint('battery', 'capacity_top_left_x'), self.cf.getint('battery', 'capacity_top_left_y'))

        # Set battery
        y = self.cf.getint('battery', 'top_left_y')
        y1 = self.cf.getint('battery', 'bottom_right_y')
        x = self.cf.getint('battery', 'top_left_x')
        x1 = self.cf.getint('battery', 'bottom_right_x')
        if 'conf/H60-L11.conf' == self.conf:
            bc_width = bc_bottom_right[0] - bc_top_left[0]
            bc_height = bc_bottom_right[1] - bc_top_left[1]
            bc_setting_width = int(bc_width * battery)
            img_bc = cv2.imread(self.cf.get(image_cf_path, 'battery_capacity'))
            img_bc = cv2.resize(img_bc, (bc_setting_width, bc_height))
            img_battery = cv2.imread(self.cf.get(image_cf_path, 'battery'))
            img_battery[bc_top_left[1]:bc_bottom_right[1], bc_top_left[0]:bc_top_left[0] + bc_setting_width] = img_bc
            img[y:y1, x:x1] = img_battery
        elif 'conf/HTC-D316d.conf' == self.conf:
            img_battery = cv2.imread(self.cf.get(image_cf_path, 'battery'))
            img_capacity = cv2.imread(self.cf.get(image_cf_path, 'battery_capacity'))
            b_width = x1 -x
            bc_height = self.cf.getint('battery', 'capacity_height')
            b_height = y1 - y
            bc_setting_height = int(bc_height*battery)
            img_capacity = cv2.resize(img_capacity, (b_width, bc_setting_height))
            img_battery[b_height-bc_setting_height:b_height, 0:b_width] = img_capacity
            img[y:y1, x:x1] = img_battery

        # Set time
        IMG_NUM_WIDTH = self.cf.getint('time', 'num_width')
        IMG_NUM_HEIGHT = self.cf.getint('time', 'num_height')
        IMG_COLON_WIDTH = self.cf.getint('time', 'colon_width')
        NUM_TOP_LEFT_WIDTH = self.cf.getint('time', 'top_left_x')
        NUM_TOP_LEFT_HEIGHT = self.cf.getint('time', 'top_left_y')

        h = NUM_TOP_LEFT_HEIGHT
        h1 = NUM_TOP_LEFT_HEIGHT + IMG_NUM_HEIGHT
        w = NUM_TOP_LEFT_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get(image_cf_path, time[0]))
        w = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get(image_cf_path, time[1]))
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get(image_cf_path, 'colon'))
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get(image_cf_path, time[3]))
        w = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 4 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get(image_cf_path, time[4]))

        return True, img

    def circle_new(self, img_path):
        ima = Image.open(img_path).convert("RGBA")
        size = ima.size
        r2 = min(size[0], size[1])
        if size[0] != size[1]:
            ima = ima.resize((r2, r2), Image.ANTIALIAS)
        circle = Image.new('L', (r2, r2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, r2, r2), fill=255)
        alpha = Image.new('L', (r2, r2), 255)
        alpha.paste(circle, (0, 0))
        ima.putalpha(alpha)
        ima.save('tmp.png')
        return cv2.imread('tmp.png')

    def circle_corder_image(self, img_path, radius=30):
        im = Image.open(img_path).convert("RGBA")
        rad = radius  # 设置半径
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        im.save('tmp-corner0.png')
        return 'tmp-corner0.png'

    def start(self):
        pass

    def compositeImage(self):
        try:
            self.start()
            return True
        except Exception as e:
            logger.error(traceback.format_exc())
            if self.driver:
                self.driver.quit()
            return False

class WebChatAutoImg(AutoImg):
    def __init__(self, time, battery, webcat_account, img_paste_ad, img_corner_mark='ads/corner-mark.png',
                 ad_type='banner', network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png'):
        AutoImg.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)
        self.webcat_account = webcat_account
        if 'banner' == ad_type:
            self.ad_width = self.cf.getint('banner', 'width')
            self.ad_height = self.cf.getint('banner', 'height')
        if 'image_text' == ad_type:
            self.ad_width = self.cf.getint('image_text', 'width')
            self.ad_height = self.cf.getint('image_text', 'height')
            self.ad_corner_width = self.cf.getint('image_text', 'corner_width')
            self.ad_corner_height = self.cf.getint('image_text', 'corner_height')
            self.ad_img_width = self.cf.getint('image_text', 'img_width')
            self.ad_img_height = self.cf.getint('image_text', 'img_height')
            self.ad_desc_pos = (self.cf.getint('image_text', 'desc_pos_x'), self.cf.getint('image_text', 'desc_pos_y'))
            self.ad_doc_pos = (self.cf.getint('image_text', 'doc_pos_x'), self.cf.getint('image_text', 'doc_pos_y'))
            self.ad_doc_pos1 = (self.cf.getint('image_text', 'doc_pos1_x'), self.cf.getint('image_text', 'doc_pos1_y'))
            desc_color = self.cf.getint('image_text', 'desc_color')
            self.ad_desc_color = (desc_color, desc_color, desc_color)
            doc_color = self.cf.getint('image_text', 'doc_color')
            self.ad_doc_color = (doc_color, doc_color, doc_color)
        if 'fine_big' == ad_type:
            self.ad_width = self.cf.getint('fine_big', 'width')
            self.ad_height = self.cf.getint('fine_big', 'height')

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.tencent.mm',
            'appActivity': '.ui.LauncherUI',
            'udid': '192.168.56.101:5555',
        }
        self.NONE = 0
        self.GOOD_MESSAGE = 1
        self.WRITE_MESSAGE = 2
        self.img_ad_message = cv2.imread(self.cf.get('image_path', 'ad_message'), 0)
        self.img_good_message = cv2.imread(self.cf.get('image_path', 'good_message'), 0)
        self.img_write_message = cv2.imread(self.cf.get('image_path', 'write_message'), 0)
        self.img_top = cv2.imread(self.cf.get('image_path', 'top'), 0)
        self.img_bottom = cv2.imread(self.cf.get('image_path', 'bottom'), 0)
        self.img_white_bkg = cv2.imread(self.cf.get('image_path', 'white_bkg'))
        self.fp_ad = str(imagehash.dhash(Image.fromarray(self.img_ad_message)))
        self.fp_good_message = str(imagehash.dhash(Image.fromarray(self.img_good_message)))
        self.fp_write_message = str(imagehash.dhash(Image.fromarray(self.img_write_message)))
        logger.debug("img_ad_message fingerprint:%s,img_good_message fingerprint:%s,img_write_message fingerprint:%s" \
              ,self.fp_ad, self.fp_good_message, self.fp_write_message)
        # All types of ad have the same distance between ad area and good_message/write_message
        self.DISTANCE_GOOD_MESSAGE = self.cf.getint('screen', 'distance_good_message')
        self.DISTANCE_WRITE_MESSAGE = self.cf.getint('screen', 'distance_write_message')

    def findAdAreaTop(self, img):
        """ Find the ad position """
        crop, top_left, bottom_right = self.findMatched(img, self.img_ad_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        logger.debug("Found img_ad_message hash is:" + fp)
        is_top = self.hammingDistOK(fp, self.fp_ad)
        return is_top, top_left, bottom_right

    def findAdAreaBottom(self, img):
        """Find good_message or write_message position"""
        crop, top_left, bottom_right = self.findMatched(img, self.img_good_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        logger.debug("Found img_good_message hash is:" + fp)
        if self.hammingDistOK(fp, self.fp_good_message):
            return self.GOOD_MESSAGE, top_left, bottom_right
        crop, top_left, bottom_right = self.findMatched(img, self.img_write_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        logger.debug("Found img_write_message hash is:" + fp)
        if self.hammingDistOK(fp, self.fp_write_message):
            return self.WRITE_MESSAGE, top_left, bottom_right
        return self.NONE, top_left, bottom_right

    def findAdArea(self, start_width, start_height, end_width, end_height):
        """We assume that ad area is less than half screen, then we have following logic"""
        cnt = 0
        while 1:
            cnt = cnt + 1
            assert cnt != 100, "Do not find webcat ad area"
            try:
                self.driver.swipe(start_width, start_height, end_width, end_height)
                self.driver.implicitly_wait(10)
                self.driver.get_screenshot_as_file("screenshot.png")
                img = cv2.imread('screenshot.png', 0)
                is_top, top_left, bottom_right = self.findAdAreaTop(img)
                if is_top: # Have found the ad position
                    #Find good_mesage or write_message
                    type, top_left1, bottom_right1 = self.findAdAreaBottom(img)
                    if self.NONE == type: #slide down to find the ad area bottom
                        return self.findAdArea_(self.screen_width / 2, self.screen_height * 3 / 5, self.screen_width / 2,
                        self.screen_height * 2/ 5)
                    break
            except Exception as e:
                logger.error('expect:' + repr(e))

        return type, (top_left[0], bottom_right[1]), (bottom_right1[0], top_left1[1])

    def findAdArea_(self, start_width, start_height, end_width, end_height):
        cnt = 0
        while 1:
            cnt = cnt + 1
            if cnt == 5:
                break
            try:
                self.driver.swipe(start_width, start_height, end_width, end_height)
                self.driver.implicitly_wait(10)
                self.driver.get_screenshot_as_file("screenshot.png")
                img = cv2.imread('screenshot.png', 0)
                is_top, top_left, bottom_right = self.findAdAreaTop(img)
                assert is_top, "Should contain ad top area"
                # Find good_mesage or write_message
                type, top_left1, bottom_right1 = self.findAdAreaBottom(img)
                if self.NONE == type: #slide down to find the ad area bottom
                    continue
                break
            except Exception as e:
                logger.error('expect:' + repr(e))
        if self.NONE == type: # There is no good_message and write_message
            crop, top_left1, bottom_right1 = self.findMatched(img, self.img_bottom)

        return type, (top_left[0], bottom_right[1]), (bottom_right1[0], top_left1[1])

    def findAdAbove(self, height, start_width, start_height, end_width, end_height):
        cnt = 0
        while 1:
            cnt = cnt + 1
            if cnt == 5:
                break
            try:
                self.driver.swipe(start_width, start_height, end_width, end_height)
                self.driver.implicitly_wait(10)
                self.driver.get_screenshot_as_file("screenshot-above.png")
                img = cv2.imread('screenshot-above.png', 0)
                is_top, top_left, bottom_right = self.findAdAreaTop(img)
                #The following comment line is useful to debug, do not remove.
                # cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
                #cv2.imwrite('./test.png', img)
                assert is_top, "Should contain ad top area"
                # Find ad above area
                img_top_crop, img_top_left, img_top_right = self.findMatched(img, self.img_top)
                if bottom_right[1] - img_top_right[1] >= height:
                    break
            except Exception as e:
                logger.error('expect:' + repr(e))

        img_color = cv2.imread("screenshot-above.png")
        return img_color[bottom_right[1] - height:bottom_right[1], 0:self.screen_width]

    def imageText(self, ad, corner_mark, desc, doc):
        """Add corner_mark, desc, doc for ad"""
        if len(desc) > self.cf.getint('image_text', 'desc_max_len'):
            desc = desc[0:self.cf.getint('image_text', 'desc_max_len')]
        if len(doc) > self.cf.getint('image_text', 'doc_max_len'):
            doc = doc[0:self.cf.getint('image_text', 'doc_max_len')]

        mask = cv2.imread(corner_mark, cv2.IMREAD_UNCHANGED)  #TODO warter mark should call self.waterMark function
        mask_gray = cv2.imread(corner_mark, 0)
        w_mask, h_mask = mask_gray.shape[::-1]
        mask_region = cv2.resize(self.img_white_bkg, (w_mask, h_mask))

        alpha_channel = mask[:, :, 3]
        rgb_channels = mask[:, :, :3]
        alpha_factor = alpha_channel[:, :, np.newaxis].astype(np.float32) / 255.0
        alpha_factor = np.concatenate((alpha_factor, alpha_factor, alpha_factor), axis=2)

        front = rgb_channels.astype(np.float32) * alpha_factor
        back = mask_region.astype(np.float32) * (1 - alpha_factor)
        final_img = front + back
        img_corner_mark = cv2.resize(final_img, (self.ad_corner_width, self.ad_corner_height))

        img_ad = cv2.imread(ad)
        img_ad = cv2.resize(img_ad, (self.ad_img_width, self.ad_img_height))
        img = cv2.resize(self.img_white_bkg, (self.ad_width, self.ad_height))
        img[0:self.ad_height, 0:self.ad_height] = img_ad
        img[self.ad_height - self.ad_corner_height:self.ad_height, self.ad_width - self.ad_corner_width:self.ad_width] = img_corner_mark
        cv2.imwrite('tuwen.png', img) #TODO convert PIL image to Opencv image directly
        ttfont = ImageFont.truetype("font/X1-55W.ttf", self.cf.getint('image_text', 'font_size'))
        im = Image.open('tuwen.png')
        draw = ImageDraw.Draw(im)
        draw.text(self.ad_desc_pos, desc, fill=self.ad_desc_color, font=ttfont) # desc could not be ''
        if self.doc1st_line > 0:
            doc_1stline_max_len = self.doc1st_line
        else:
            doc_1stline_max_len = self.set1stDocLen(doc)
        if len(doc) <= doc_1stline_max_len: # 15 utf-8 character in one line should be OK usually
            draw.text(self.ad_doc_pos, doc, fill=self.ad_doc_color, font=ttfont) # doc could not be ''
        else:
            draw.text(self.ad_doc_pos, doc[:doc_1stline_max_len], fill=self.ad_doc_color, font=ttfont)  # doc could not be ''
            draw.text(self.ad_doc_pos1, doc[doc_1stline_max_len:], fill=self.ad_doc_color, font=ttfont)  # doc could not be ''
        im.save('tuwen.png')

        return True, cv2.imread('tuwen.png')

    def set1stDocLen(self, doc):
        cl = self.cf.getint('image_text', 'doc_Chinese_width')
        el = self.cf.getint('image_text', 'doc_English_width')
        fl = self.cf.getint('image_text', 'doc_1stline_px_len')
        mlen = 0
        for i in range(len(doc)):
            if doc[i] <= '\u2000':
                mlen += el
            # I think Chinese and Chinese punctuation(eg:，。：) consume doc_Chinese_width length px
            else:
                mlen += cl
            if mlen > fl:
                logger.debug('doc first line len is:%d', i)
                return i

        return len(doc)

    def clickTarget(self, target, type='name'):
        cnt = 0;
        while 1:
            cnt = cnt + 1
            assert cnt != 15, "Do not find webaccount %s" %(target)
            try:
                if 1 != cnt:
                    self.driver.swipe(self.screen_width / 2, self.screen_height * 2 / 3, self.screen_width / 2,
                                      self.screen_height * 1 / 3)
                    self.driver.implicitly_wait(5)
                return self.driver.find_element_by_name(target).click()
                break
            except:
                continue

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(30) #Webcat may start slowly, so set waiting time to be long
        self.driver.find_element_by_name(u"通讯录").click()
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_name(u"公众号").click()
        self.driver.implicitly_wait(10)
        el = self.clickTarget(self.webcat_account)
        self.driver.implicitly_wait(10)
        action = TouchAction(self.driver)
        random_y = random.randint(self.cf.getint('article_pos', 'y_min'), self.cf.getint('article_pos', 'y_max'))
        action.tap(el, self.cf.getint('article_pos', 'x'), random_y).perform()
        #self.driver.find_element_by_id('com.tencent.mm:id/fl').click()
        sleep(1)

        ad_bottom_type, left, right = self.findAdArea(self.screen_width / 2, self.screen_height * 3 / 4, self.screen_width / 2,
                        self.screen_height / 4)
        logger.debug("bottom type:%d", ad_bottom_type)

        img_color = cv2.imread('screenshot.png')
        # Compare ad area and area we need
        area_height = right[1] - left[1]
        img_gray = cv2.imread('screenshot.png', 0)
        wanted_height = self.ad_height
        if ad_bottom_type == self.GOOD_MESSAGE:
            wanted_height += self.DISTANCE_GOOD_MESSAGE
        elif ad_bottom_type == self.WRITE_MESSAGE:
            wanted_height += self.DISTANCE_WRITE_MESSAGE

        # ad aread is bigger than wanted, should shrink
        if area_height - wanted_height > 3:
            logger.debug("Should shrink ad area")
            #  Calculate ad area
            left = (0, left[1] + (area_height - wanted_height))
            # Calculate ad top area
            crop, img_top_left, img_top_right = self.findMatched(img_gray, self.img_top)
            ad_above_height = left[1] - img_top_right[1]
            ad_above = self.findAdAbove(ad_above_height, self.screen_width / 2, self.screen_height * 2 / 5, self.screen_width / 2,
                        self.screen_height * 3/ 5)

        # ad area is smaller than wanted, should enlarge
        if area_height - wanted_height < -3:
            logger.debug("Should enlarge ad area")
            # Calculate ad top area
            crop, img_top_left, img_top_right = self.findMatched(img_gray, self.img_top)
            ad_above = img_color[img_top_right[1]+wanted_height-area_height:left[1], 0:self.screen_width]
            # update ad area
            left = (0, left[1] + area_height - wanted_height)

        # if ad area size changed, set area ad above
        if abs(area_height - wanted_height) > 3:
            img_color[img_top_right[1]:left[1], 0:self.screen_width] = ad_above

        # Paint ad area to be blank
        img_blank = cv2.imread(self.ad_area_path + 'blank.png')
        img_blank_resize = cv2.resize(img_blank, (right[0] - left[0], right[1] - left[1]))
        img_color[left[1]:right[1], left[0]:right[0]] = img_blank_resize

        # Add our ad image
        if 'image_text' != self.ad_type:
            img_ad = self.warterMark(self.img_paste_ad, self.img_corner_mark)
            img_ad_resize = cv2.resize(img_ad, (self.ad_width, self.ad_height))
        else:
            _, img_ad_resize = self.imageText(self.img_paste_ad, self.img_corner_mark, self.desc, self.doc)
        left_side = (self.screen_width-self.ad_width)/2
        img_color[left[1]:left[1]+self.ad_height, left_side:left_side+self.ad_width] = img_ad_resize

        # Add header image
        ok, img_header = self.header(self.time, self.battery, self.network)
        if ok:
            img_color[0:self.ad_header_height, 0:self.ad_header_width] = img_header

        cv2.imwrite(self.composite_ads_path, img_color)

        sleep(3)
        self.driver.quit()

class QQAutoImg(AutoImg):
    def __init__(self, plugin, city, time, battery, img_paste_ad, img_corner_mark='ads/corner-mark.png',
                 ad_type='banner', network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', logo=''):
        AutoImg.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path)

        self.plugin = plugin

        # Set weather args
        if 'weather' == plugin:
            self.city = city
            self.img_hot_city = cv2.imread(self.cf.get('image_path', 'hot_city'), 0)
            self.fp_hot_city = str(imagehash.dhash(Image.fromarray(self.img_hot_city)))
            logger.debug("plugin:%s, city:%s", self.plugin, self.city)
            logger.debug("img_hot_city fingerprint:%s", self.fp_hot_city)
            self.general_cities = ['hefei', 'fuzhou', 'wuhan']
            self.city_pre = {'hefei':'H', 'fuzhou':'F', 'wuhan':'W'}

        # Set feeds args
        if 'feeds' == plugin:
            self.logo = logo
            self.ad_flag = cv2.imread(self.cf.get('image_path', 'feeds_ad'), 0)
            self.fp_ad_flag = str(imagehash.dhash(Image.fromarray(self.ad_flag)))
            self.split = cv2.imread(self.cf.get('image_path', 'feeds_split'), 0)
            self.fp_split = str(imagehash.dhash(Image.fromarray(self.split)))
            logger.debug("fp_ad_flag:%s, fp_split:%s", self.fp_ad_flag, self.fp_split)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.2.2',
            'deviceName': 'Genymotion Phone - 4.2.2 - API 17 - 2.9.0',
            'appPackage': 'com.tencent.mobileqq',
            'appActivity': '.activity.SplashActivity',
            'udid': '192.168.56.101:5555',
        }

    def findHotCity(self, img):
        """ Find the hot city position """
        crop, top_left, bottom_right = self.findMatched(img, self.img_hot_city)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        logger.debug("Found hot city fp is:" + fp)
        is_hot_city = self.hammingDistOK(fp, self.fp_hot_city)
        return is_hot_city, top_left, bottom_right

    def weatherStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        el = self.driver.find_element_by_name(u"联系人").click()
        self.driver.implicitly_wait(30)
        action = TouchAction(self.driver)
        action.tap(el, self.cf.getint('QQ_icon', 'x'), self.cf.getint('QQ_icon', 'y')).perform()
        sleep(1)
        el = self.driver.find_element_by_name(u"o").click()
        self.driver.implicitly_wait(10)
        sleep(10)

        #Click switch city
        if 'shanghai' != self.city:
            action.tap(el, self.cf.getint('QQ_weather', 'switch_x'), self.cf.getint('QQ_weather', 'switch_y')).perform()
            sleep(2)
            self.driver.get_screenshot_as_file("screenshot.png")

            #Choose city page may have GPS info, have or have not GPS info, hot city' position is different,
            #So find hot city img to get city' precise position
            img = cv2.imread('screenshot.png', 0)
            is_hot_city, top_left, bottom_right = self.findHotCity(img)
            logger.debug("is_hot_city:%d, top_left[0]:%d, top_left[1]:%d, bottom_right[0]:%d, bottom_right[1]:%d",
                          is_hot_city, top_left[0], top_left[1], bottom_right[0], bottom_right[1])
            #cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
            #cv2.imwrite('hot_city.png', img)
            if self.city not in self.general_cities:
                x = self.cf.getint('QQ_weather', self.city+"_x") + top_left[0]
                y = self.cf.getint('QQ_weather', self.city+"_y") + top_left[1]
                action.tap(el, x, y).perform()
            else:
                x = self.cf.getint('QQ_weather', self.city_pre[self.city] + "_x") + top_left[0]
                y = self.cf.getint('QQ_weather', self.city_pre[self.city] + "_y") + top_left[1]
                action.tap(el, x, y).perform()
                sleep(0.5)
                x = self.cf.getint('QQ_weather', self.city + "_x")
                y = self.cf.getint('QQ_weather', self.city + "_y")
                action.tap(el, x, y).perform()
            sleep(10)
            self.driver.get_screenshot_as_file("screenshot.png")
        else:
            self.driver.get_screenshot_as_file("screenshot.png")

        ad_weather = cv2.resize(cv2.imread(self.img_paste_ad), ((self.cf.getint('QQ_weather', 'ad_width'),
                                                    self.cf.getint('QQ_weather', 'ad_height'))))
        cv2.imwrite('ad_weather.png', ad_weather)

        ad_watermark = self.warterMark('ad_weather.png', self.img_corner_mark, 'top_right')
        im = cv2.imread('screenshot.png')
        im[self.cf.getint('QQ_weather', 'ad_top_left_y'):self.cf.getint('QQ_weather', 'ad_bottom_right_y'),
        self.cf.getint('QQ_weather', 'ad_top_left_x'):self.cf.getint('QQ_weather', 'ad_bottom_right_x')] \
            = ad_watermark

        ok, img_header = self.header(self.time, self.battery, self.network, 'QQ_weather')
        if ok:
            im[0:self.ad_header_height, 0:self.ad_header_width] = img_header
        #Set weather header, so its theme looks like "白色"主题
        im[self.cf.getint('QQ_weather', 'header_y1'):self.cf.getint('QQ_weather', 'header_y2'),
            0:self.screen_width] = cv2.imread(self.cf.get('QQ_weather', 'weather_header'))

        cv2.imwrite(self.composite_ads_path, im)
        self.driver.quit()

    def swipe(self, start_width, start_height, end_width, end_height):
        """"Meet error when swipe in QQ dongtai, use this function to swipe even meeting error
        """
        try:
            self.driver.swipe(start_width, start_height, end_width, end_height)
            self.driver.implicitly_wait(10)
        except Exception as e:
            pass

    def findAdArea(self, start_width, start_height, end_width, end_height):
        """ QQ dongtai will push ad in the beginning dongtai.
            So insert one ad between the first few dongtai.
        """
        for _ in (0, random.randint(0, 2)):
            self.swipe(start_width, start_height, end_width, end_height)
        cnt = 0
        while 1:
            cnt = cnt + 1
            assert cnt != 10, "Do not find ad area"
            try:
                self.swipe(start_width, start_height, end_width, end_height)
                self.driver.get_screenshot_as_file("screenshot.png")
                img = cv2.imread('screenshot.png', 0)
                ok, top_left, bottom_right = self.findMatchedArea(img, self.split, self.fp_split)
                if ok:
                    # Do not insert ad in page which has already had an ad
                    has_ad_flag, _, _ = self.findMatchedArea(img, self.ad_flag, self.fp_ad_flag)
                    if has_ad_flag:
                        continue
                    if self.screen_height - bottom_right[1] < self.cf.getint('QQFeeds', 'blank_height') + 3:
                        continue
                    break
            except Exception as e:
                logger.error('expect:' + repr(e))
#
        cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
        cv2.imwrite('feeds.png', img)
        return top_left, bottom_right

    def assembleFeedsAd(self):
        blank_height = self.cf.getint('QQFeeds', 'blank_height')
        flag_x = self.cf.getint('QQFeeds', 'flag_x')
        flag_y = self.cf.getint('QQFeeds', 'flag_y')
        flag_width = self.cf.getint('QQFeeds', 'flag_width')
        flag_height = self.cf.getint('QQFeeds', 'flag_height')
        logo_radius = self.cf.getint('QQFeeds', 'logo_radius')
        logo_x = self.cf.getint('QQFeeds', 'logo_x')
        logo_y = self.cf.getint('QQFeeds', 'logo_y')
        line_y = self.cf.getint('QQFeeds', 'line_y')
        split_height = self.cf.getint('QQFeeds', 'split_height')

        ad_width = self.cf.getint('QQFeeds', 'ad_width')
        ad_height = self.cf.getint('QQFeeds', 'ad_height')
        ad_bk_width = self.cf.getint('QQFeeds', 'ad_bk_width')
        ad_bk_height = self.cf.getint('QQFeeds', 'ad_bk_height')
        ad_bk_x = (self.screen_width - ad_width) / 2
        ad_bk_y = self.cf.getint('QQFeeds', 'ad_bk_y')
        ad_bk_radius = self.cf.getint('QQFeeds', 'ad_bk_radius')
        recom_width = self.cf.getint('QQFeeds', 'recom_width')
        reocm_height = self.cf.getint('QQFeeds', 'recom_height')

        blank = cv2.imread(self.cf.get('image_path', 'feeds_blank'))
        bkg = cv2.resize(blank, (self.screen_width, blank_height))
        # Add logo
        logo = self.circle_new(self.logo)
        logo = cv2.resize(logo, (logo_radius, logo_radius))
        bkg[logo_y:logo_y+logo_radius, logo_x:logo_x+logo_radius] = logo
        # Add flag
        bkg[flag_y:flag_y+flag_height, flag_x:flag_x+flag_width] = cv2.imread(self.cf.get('image_path', 'feeds_ad'))
        # Add line
        bkg[line_y:line_y+1, 0:self.screen_width] = cv2.imread(self.cf.get('image_path', 'feeds_line'))

        # Add split
        bkg[blank_height-split_height:blank_height, 0:self.screen_width] \
            = cv2.imread(self.cf.get('image_path', 'feeds_split'))

        # Add ad and recomment
        ad_bk = cv2.imread(self.cf.get('image_path', 'feeds_ad_bk'))
        ad = cv2.imread(self.img_paste_ad)
        ad = cv2.resize(ad, (ad_width, ad_height))
        ad_bk[1:1+ad_height, 1:1+ad_width] = ad
        ad_bk[1+ad_height:1+ad_height+reocm_height, 1:1+recom_width] \
            = cv2.imread(self.cf.get('image_path', 'feeds_recom'))
        cv2.imwrite('tmp.png', ad_bk)
        ad_bk_img = self.circle_corder_image('tmp.png', ad_bk_radius)
        cv2.imwrite('tmp.png', cv2.resize(blank, (ad_bk_width, ad_bk_height)))
        ad_bk_ = self.warterMark('tmp.png', ad_bk_img)
        #TODO, if doc has two lines, should calculate ad_bk position
        bkg[ad_bk_y:ad_bk_y+ad_bk_height, ad_bk_x:ad_bk_x+ad_bk_width] = ad_bk_

        cv2.imwrite('tmp.png', bkg)

        # Print doc and desc in the bkg
        #ttfont = ImageFont.truetype("font/X1-55W.ttf", self.cf.getint('QQFeeds', 'doc_size'))
        #im = Image.open('browser.png')
        #draw = ImageDraw.Draw(im)
        #draw.text(self.ad_doc_pos, self.doc, fill=self.ad_doc_color, font=ttfont)  # desc could not be ''
        #ttfont_ = ImageFont.truetype("font/X1-55W.ttf", self.cf.getint('QQFeeds', 'desc_size'))
        #draw.text(self.ad_desc_pos, self.desc, fill=self.ad_desc_color, font=ttfont_)
        #im.save('tmp.png')

        return cv2.imread('tmp.png')

    def feedsStart(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_name(u"动态").click()
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_name(u"好友动态").click()
        self.driver.implicitly_wait(10)
        sleep(5)
        top_left, bottom_right = self.findAdArea(self.screen_width / 2, self.screen_height * 3 / 4,
                                                 self.screen_width / 2, self.screen_height / 4)
        ad = self.assembleFeedsAd()
        #self.driver.get_screenshot_as_file('screenshot.png')

        self.driver.quit()

    def compositeImage(self):
        try:
            if 'weather' == self.plugin:
                self.weatherStart()
                return True
            if 'feeds' == self.plugin:
                self.feedsStart()
                return True
        except Exception as e:
            logger.error(traceback.format_exc())
            if self.driver:
                self.driver.quit()
            return False

class QQBrowserAutoImg(AutoImg):
    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ad_area/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png', conf='conf/HTC-D316d.conf'):
        AutoImg.__init__(self, time, battery, img_paste_ad, img_corner_mark, ad_type, network, desc,
                         doc, doc1st_line, save_path, conf)

        self.ad_flag = cv2.imread(self.cf.get('image_path', 'browser_ad'), 0)
        self.fp_ad_flag = str(imagehash.dhash(Image.fromarray(self.ad_flag)))
        self.hot_header = cv2.imread(self.cf.get('image_path', 'browser_hot_header'), 0)
        self.fp_hot_header = str(imagehash.dhash(Image.fromarray(self.hot_header)))
        self.split = cv2.imread(self.cf.get('image_path', 'browser_split'), 0)
        self.fp_split = str(imagehash.dhash(Image.fromarray(self.split)))

        self.ad_desc_pos = (self.cf.getint('QQBrowser', 'desc_x'), self.cf.getint('QQBrowser', 'desc_y'))
        desc_color = self.cf.getint('QQBrowser', 'desc_color')
        self.ad_desc_color = (desc_color, desc_color, desc_color)
        self.ad_doc_pos = (self.cf.getint('QQBrowser', 'doc_x'), self.cf.getint('QQBrowser', 'doc_y'))
        doc_color = self.cf.getint('QQBrowser', 'doc_color')
        self.ad_doc_color = (doc_color, doc_color, doc_color)

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.3',
            'deviceName': 'HTC D316d',
            'appPackage': 'com.tencent.mtt',
            'appActivity': '.MainActivity',
            'udid': '0123456789ABCDEF',
        }
    def findAdArea(self, start_width, start_height, end_width, end_height):
        """ We assume that ad area is less than half screen, then we have following logic.
            QQBrowser will not push ad when accessed too much!!! so insert one ad between news area.
        """
        for _ in (0,random.randint(2, 20)):
            self.driver.swipe(start_width, start_height, end_width, end_height)
            self.driver.implicitly_wait(10)
        cnt = 0
        while 1:
            cnt = cnt + 1
            assert cnt != 10, "Do not find ad area"
            try:
                self.driver.swipe(start_width, start_height, end_width, end_height)
                self.driver.implicitly_wait(10)
                self.driver.get_screenshot_as_file("screenshot.png")
                img = cv2.imread('screenshot.png', 0)
                ok, top_left, bottom_right = self.findMatchedArea(img, self.split, self.fp_split)
                if ok:
                    # Do not insert ad in page which has already had an ad
                    has_ad_flag, _, _ = self.findMatchedArea(img, self.ad_flag, self.fp_ad_flag)
                    if has_ad_flag:
                        continue
                    #TODO When doc line is 2, ad area height will be bigger than blank_height, should consider this
                    if self.cf.getint('QQBrowser', 'bottom_y') - top_left[1] < self.cf.getint('QQBrowser', 'blank_height') + 3:
                        continue
                    break
            except Exception as e:
                logger.error('expect:' + repr(e))

        return top_left, bottom_right

    def assembleImg(self):
        blank_height = self.cf.getint('QQBrowser', 'blank_height')
        ad_width = self.cf.getint('QQBrowser', 'ad_width')
        ad_height = self.cf.getint('QQBrowser', 'ad_height')
        split_ad_dis = self.cf.getint('QQBrowser', 'split_ad_dis')
        flag_x = self.cf.getint('QQBrowser', 'flag_x')
        flag_y = self.cf.getint('QQBrowser', 'flag_y')
        flag_width = self.cf.getint('QQBrowser', 'flag_width')
        flag_height = self.cf.getint('QQBrowser', 'flag_height')
        ad_x = (self.screen_width - ad_width) / 2

        blank = cv2.imread(self.cf.get('image_path', 'browser_blank'))
        bkg = cv2.resize(blank, (self.screen_width, blank_height))
        ad = cv2.imread(self.img_paste_ad)

        paste_ad = cv2.resize(ad, (ad_width, ad_height))
        bkg[split_ad_dis:split_ad_dis+ad_height, ad_x:ad_x+ad_width] = paste_ad

        bkg[blank_height - 1:blank_height, 0:self.screen_width] = cv2.imread(self.cf.get('image_path', 'browser_split'))
        bkg[flag_y:flag_y+flag_height, flag_x:flag_x+flag_width] = cv2.imread(self.cf.get('image_path', 'browser_ad'))
        cv2.imwrite('browser.png', bkg)

        # Print doc and desc in the bkg
        ttfont = ImageFont.truetype("font/X1-55W.ttf", self.cf.getint('QQBrowser', 'doc_size'))
        im = Image.open('browser.png')
        draw = ImageDraw.Draw(im)
        draw.text(self.ad_doc_pos, self.doc, fill=self.ad_doc_color, font=ttfont)  # desc could not be ''
        ttfont_ = ImageFont.truetype("font/X1-55W.ttf", self.cf.getint('QQBrowser', 'desc_size'))
        draw.text(self.ad_desc_pos, self.desc, fill=self.ad_desc_color, font=ttfont_)
        im.save('browser.png')

        return cv2.imread('browser.png')

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

        ad = self.assembleImg()
        img = cv2.imread('screenshot.png')
        bottom_y = self.cf.getint('QQBrowser', 'bottom_y')
        blank_height = self.cf.getint('QQBrowser', 'blank_height')
        ad_bottom_height = bottom_y - bottom_right[1] - blank_height
        img[bottom_y-ad_bottom_height: bottom_y,0:self.screen_width] = \
            img[bottom_right[1]:bottom_right[1]+ad_bottom_height, 0:self.screen_width]
        img[bottom_right[1]:bottom_right[1]+blank_height, 0:self.screen_width] = ad

        ok, img_header = self.header(self.time, self.battery, self.network)
        if ok:
            img[0:self.ad_header_height, 0:self.ad_header_width] = img_header
        #cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
        cv2.imwrite(self.composite_ads_path, img)
        self.driver.quit()

if __name__ == '__main__':
    try:
        title = u'上海老公房8万翻新出豪宅感！'
        doc = u'输入你家房子面积，算一算装修该花多少钱？'
        autoImg = WebChatAutoImg('16:20', 1, u'汽车之家', 'ads/114x114-1.jpg', 'ad_area/corner-mark.png', 'image_text',
                                 'wifi', title, doc)
        #autoImg = AutoImg(args.time, args.battery, args.webaccount, args.ad, args.corner, args.type, args.network,
        #                  args.title, args.doc)
        #autoImg = QQAutoImg('feeds', '', '16:20', 1, 'ads/feeds1000x560.jpg', 'ads/logo_512x512.jpg', 'image_text', 'wifi')
        #autoImg = QQAutoImg('weather', 'shanghai', '11:49', 0.5, 'ads/4.jpg', 'ad_area/corner-ad.png', 'image_text', '4G')
        #autoImg = QQBrowserAutoImg('16:20', 0.5, 'ads/browser_ad.jpg', 'ad_area/corner-ad.png', 'image_text', 'wifi',
        #                           u'吉利新帝豪', u'新帝豪八周年钜惠14000元！')
        autoImg.compositeImage()

        #img = cv2.imread('ad_area/HTC-D316d/browser_split.png')
        #line = img[2:3, 0:540]
        #ad_bk = cv2.resize(line, (680, 481))
        #cv2.imwrite('browser_split.png', line)
    except Exception as e:
        traceback.print_exc()
