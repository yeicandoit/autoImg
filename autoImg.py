#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import numpy as np
import traceback
import ConfigParser
import argparse
from appium.webdriver.common.touch_action import TouchAction
import logging
logger = logging.getLogger('main.autoImg')

class AutoImg:
    def __init__(self, time, battery, webcat_account, img_paste_ad, img_corner_mark='ads/corner-mark.png',
                 ad_type='banner', network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png'):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read('conf/H60-L11.conf')

        self.time = time
        self.battery = battery
        self.webcat_account = webcat_account.decode('utf-8')
        self.img_paste_ad = img_paste_ad
        self.img_corner_mark = img_corner_mark
        self.ad_type = ad_type
        self.network = network
        #self.desc = desc.decode('utf-8')
        #self.doc = doc.decode('utf-8')
        self.desc = desc
        self.doc = doc
        self.doc1st_line = doc1st_line

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

        self.composite_ads_path = save_path
        self.ad_area_path = 'ad_area/'

        self.desired_caps = {
            'platformName': 'Android',
            'platformVersion': '4.4.2',
            'deviceName': 'H60-L11',
            'appPackage': 'com.tencent.mm',
            'appActivity': '.ui.LauncherUI',
            'chromeOptions': {
                'androidProcess': 'com.tencent.mm:tools'
            }
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

        self.screen_width = self.cf.getint('screen', 'width')
        self.screen_height = self.cf.getint('screen', 'height')
        self.ad_header_width = self.cf.getint('screen', 'header_width')
        self.ad_header_height = self.cf.getint('screen', 'header_height')
        # All types of ad have the same distance between ad area and good_message/write_message
        self.DISTANCE_GOOD_MESSAGE = self.cf.getint('screen', 'distance_good_message')
        self.DISTANCE_WRITE_MESSAGE = self.cf.getint('screen', 'distance_write_message')

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
            if cnt == 100:
                break
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

    def warterMark(self, ad, corner_mark):
        """Add corner_mark on right_bottom for ad"""
        img = cv2.imread(ad)
        img_gray = cv2.imread(ad, 0)
        mask = cv2.imread(corner_mark, cv2.IMREAD_UNCHANGED)
        mask_gray = cv2.imread(corner_mark, 0)
        w_mask, h_mask = mask_gray.shape[::-1]
        w_img, h_img = img_gray.shape[::-1]
        mask_region = img[h_img - h_mask:h_img, w_img - w_mask:w_img]

        alpha_channel = mask[:, :, 3]
        rgb_channels = mask[:, :, :3]
        alpha_factor = alpha_channel[:, :, np.newaxis].astype(np.float32) / 255.0
        alpha_factor = np.concatenate((alpha_factor, alpha_factor, alpha_factor), axis=2)

        front = rgb_channels.astype(np.float32) * alpha_factor
        back = mask_region.astype(np.float32) * (1 - alpha_factor)
        final_img = front + back
        img[h_img - h_mask:h_img, w_img - w_mask:w_img] = final_img
        return img

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

    def header(self, time, battery, network):
        """set time and network. Time looks like 14:01. network is 3G, 4G and wifi"""
        if len(time) < 5:
            return False, None
        if battery > self.cf.getfloat('battery', 'capacity_max') or battery < self.cf.getfloat('battery', 'capacity_min'):
            return  False, None
        if network != '3G' and network != '4G' and network != 'wifi':
            return False, None

        # Set network
        img = cv2.imread(self.cf.get('image_path', network))

        # battery capacity position in battery
        bc_bottom_right = (self.cf.getint('battery', 'capacity_bottom_right_x'), self.cf.getint('battery', 'capacity_bottom_right_y'))
        bc_top_left = (self.cf.getint('battery', 'capacity_top_left_x'), self.cf.getint('battery', 'capacity_top_left_y'))

        # Set battery
        bc_width = bc_bottom_right[0] - bc_top_left[0]
        bc_height = bc_bottom_right[1] - bc_top_left[1]
        bc_setting_width = int(bc_width * battery)
        img_bc = cv2.imread(self.ad_area_path + 'battery-capacity.png')
        img_bc = cv2.resize(img_bc, (bc_setting_width, bc_height))
        img_battery = cv2.imread(self.ad_area_path + 'battery.png')
        img_battery[bc_top_left[1]:bc_bottom_right[1], bc_top_left[0]:bc_top_left[0] + bc_setting_width] = img_bc
        y = self.cf.getint('battery', 'top_left_y')
        y1 = self.cf.getint('battery', 'bottom_right_y')
        x = self.cf.getint('battery', 'top_left_x')
        x1 = self.cf.getint('battery', 'bottom_right_x')
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
        img[h:h1, w:w1] = cv2.imread(self.cf.get('image_path', time[0]))
        w = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get('image_path', time[1]))
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get('image_path', 'colon'))
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get('image_path', time[3]))
        w = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 4 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.cf.get('image_path', time[4]))

        return True, img

    def clickTarget(self, target, type='name'):
        cnt = 0;
        while 1:
            cnt = cnt + 1
            if cnt == 10:
                break
            try:
                return self.driver.find_element_by_name(target).click()
                break
            except:
                self.driver.swipe(self.screen_width / 2, self.screen_height * 3 / 4, self.screen_width / 2,
                        self.screen_height / 4)
                self.driver.implicitly_wait(10)
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
        action.tap(el, self.cf.getint('article_pos', 'x'), self.cf.getint('article_pos', 'y')).perform()
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
    def compositeImage(self):
        try:
            self.start()
            return True
        except Exception as e:
            logger.error(traceback.format_exc())
            self.driver.quit()
            return False

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="progrom description")
        parser.add_argument('-t', '--time', required=True, help="时间")
        parser.add_argument('-b', '--battery', type=float, required=True, help='电量')
        parser.add_argument('-w', '--webaccount', required=True, help='公众号')
        parser.add_argument('-a', '--ad', required=True, help='广告')
        parser.add_argument('-c', '--corner', required=True, help='角标')
        parser.add_argument('-at', '--type', default='banner', help='广告类型')
        parser.add_argument('-n', '--network', default='wifi', help='网络类型')
        parser.add_argument('-ti', '--title', default='', help='图文广告标题')
        parser.add_argument('-d', '--doc', default='', help='图文广告文案')

        args = parser.parse_args()
        #title = '上海老公房8万翻新出豪宅感！'
        #doc = '输入你家房子面积，算一算装修该花多少钱？'
        #autoImg = AutoImg('16:20', 1, '爱健身', 'ads/114x114-1.jpg', 'ads/corner-mark.png', 'image_text', 'wifi', title, doc)
        autoImg = AutoImg(args.time, args.battery, args.webaccount, args.ad, args.corner, args.type, args.network,
                          args.title, args.doc)
        autoImg.start()
    except Exception as e:
        traceback.print_exc()
