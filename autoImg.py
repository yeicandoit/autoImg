#coding=utf-8
from appium import webdriver
from time import sleep
from PIL import Image,ImageDraw,ImageFont
import cv2
import imagehash
import numpy as np


class AutoImg:
    def __init__(self, time, battery, webcat_account, img_paste_ad, img_corner_mark='ads/corner-mark.png', ad_type='banner', network='wifi', desc='', doc=''):
        self.time = time
        self.battery = battery
        self.webcat_account = webcat_account.decode('utf-8')
        self.img_paste_ad = img_paste_ad
        self.img_corner_mark = img_corner_mark
        self.ad_type = ad_type
        self.network = network
        self.desc = desc.decode('utf-8')
        self.doc = doc.decode('utf-8')

        if 'banner' == ad_type:
            self.ad_width = 660
            self.ad_height = 188
        if 'image-text' == ad_type:
            self.ad_width = 656
            self.ad_height = 178
            self.ad_corner_width = 157
            self.ad_corner_height = 42
            self.ad_img_width = 178
            self.ad_img_height = 178
            self.ad_desc_pos = (209, 26)
            self.ad_doc_pos = (209, 66)
            self.ad_doc_pos1 = (209, 102)
            self.ad_desc_color = (55, 55, 55)
            self.ad_doc_color = (144, 144, 144)
        if 'fine-big' == ad_type:
            self.ad_width = 660
            self.ad_height = 372

        self.composite_ads_path = 'composite_ads/'
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

        self.img_ad = cv2.imread(self.ad_area_path + 'template.png',0)
        self.img_good_message = cv2.imread(self.ad_area_path + 'good_message.png', 0)
        self.img_write_message = cv2.imread(self.ad_area_path + 'write_message.png', 0)
        self.img_top = cv2.imread(self.ad_area_path + 'top.png', 0)
        self.img_bottom = cv2.imread(self.ad_area_path + 'bottom.png', 0)
        self.img_white_bkg = cv2.imread(self.ad_area_path + 'white_bkg.png')
        self.fp_ad = str(imagehash.dhash(Image.fromarray(self.img_ad)))
        self.fp_good_message = str(imagehash.dhash(Image.fromarray(self.img_good_message)))
        self.fp_write_message = str(imagehash.dhash(Image.fromarray(self.img_write_message)))
        print "img_ad fingerprint: %s\nimg_good_message fingerprint: %s\nimg_write_message fingerprint:%s" \
              %(self.fp_ad, self.fp_good_message, self.fp_write_message)

        self.screen_width = 720
        self.screen_height = 1280
        self.ad_header_width = 720
        self.ad_header_height = 50
        # All types of ad have the same distance between ad area and good_message/write_message
        self.DISTANCE_GOOD_MESSAGE = 115
        self.DISTANCE_WRITE_MESSAGE = 80

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
        print top_left[0], top_left[1], bottom_right[0], bottom_right[1]
        crop = src[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        return crop, top_left, bottom_right

    def findAdAreaTop(self, img):
        """ Find the ad position """
        crop, top_left, bottom_right = self.findMatched(img, self.img_ad)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        print ("Found img_ad hash is:" + fp)
        is_top = self.hammingDistOK(fp, self.fp_ad)
        return is_top, top_left, bottom_right

    def findAdAreaBottom(self, img):
        """Find good_message or write_message position"""
        crop, top_left, bottom_right = self.findMatched(img, self.img_good_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        print ("Found img_good_message hash is:" + fp)
        if self.hammingDistOK(fp, self.fp_good_message):
            return self.GOOD_MESSAGE, top_left, bottom_right
        crop, top_left, bottom_right = self.findMatched(img, self.img_write_message)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        print ("Found img_write_message hash is:" + fp)
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
                print('expect:' + repr(e))

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
                print('expect:' + repr(e))
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
                assert is_top, "Should contain ad top area"
                # Find ad above area
                img_top_crop, img_top_left, img_top_right = self.findMatched(img, self.img_top)
                if bottom_right[1] - img_top_right[1] >= height:
                    break
            except Exception as e:
                print('expect:' + repr(e))

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
        img_ad = cv2.resize(img_ad, (178, 178))
        img = cv2.resize(self.img_white_bkg, (self.ad_width, self.ad_height))
        img[0:self.ad_height, 0:self.ad_height] = img_ad
        img[self.ad_height - self.ad_corner_height:self.ad_height, self.ad_width - self.ad_corner_width:self.ad_width] = img_corner_mark
        cv2.imwrite('tuwen.png', img) #TODO convert PIL image to Opencv image directly
        ttfont = ImageFont.truetype("font/X1-55W.ttf", 30)
        im = Image.open('tuwen.png')
        draw = ImageDraw.Draw(im)
        draw.text(self.ad_desc_pos, desc, fill=self.ad_desc_color, font=ttfont) # desc could not be ''
        draw.text(self.ad_doc_pos, doc, fill=self.ad_doc_color, font=ttfont) # doc could not be ''
        im.save('tuwen.png')

        return cv2.imread('tuwen.png')

    def header(self, time, battery, network):
        """set time and network. Time looks like 14:01. network is 3G, 4G and wifi"""
        #TODO set position in __init__ function
        if len(time) < 5:
            return False, None
        if battery > 1 or battery < 0.2:
            return  False, None
        if network != '3G' and network != '4G' and network != 'wifi':
            return False, None

        # Set network
        img = cv2.imread(self.ad_area_path + 'margin_top_' + network + '.png')

        # Set battery
        #battery_bottom_right = (621, 33)
        #battery_top_left = (591, 17)
        #battery_width = battery_bottom_right[0] - battery_top_left[0]
        #battery_height = battery_bottom_right[1] - battery_top_left[1]
        #battery_setting_width = int(battery_width * battery)
        #img_battery = cv2.imread(self.ad_area_path + 'battery.png')
        #img_battery = cv2.resize(img_battery, (battery_setting_width, battery_height))
        #img[battery_top_left[1]:battery_bottom_right[1], battery_top_left[0]:battery_top_left[0]+battery_setting_width] = img_battery

        bc_bottom_right = (34, 20) # battery capacity position in battery
        bc_top_left = (4, 4) # battery capacity position in battery
        bc_width = bc_bottom_right[0] - bc_top_left[0]
        bc_height = bc_bottom_right[1] - bc_top_left[1]
        bc_setting_width = int(bc_width * battery)
        img_bc = cv2.imread(self.ad_area_path + 'battery-capacity.png')
        img_bc = cv2.resize(img_bc, (bc_setting_width, bc_height))
        img_battery = cv2.imread(self.ad_area_path + 'battery.png')
        img_battery[bc_top_left[1]:bc_bottom_right[1], bc_top_left[0]:bc_top_left[0] + bc_setting_width] = img_bc
        # battery position is (586, 13), (627, 37), TODO set the position in __init__ function
        img[14:38, 586:627] = img_battery

        # Set time
        IMG_NUM_WIDTH = 16
        IMG_NUM_HEIGHT = 24
        IMG_COLON_WIDTH = 7
        NUM_TOP_LEFT_WIDTH = 637
        NUM_TOP_LEFT_HEIGHT = 14

        h = NUM_TOP_LEFT_HEIGHT
        h1 = NUM_TOP_LEFT_HEIGHT + IMG_NUM_HEIGHT
        w = NUM_TOP_LEFT_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.ad_area_path + time[0] + '.png')
        w = NUM_TOP_LEFT_WIDTH + IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.ad_area_path + time[1] + '.png')
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.ad_area_path + 'colon.png')
        w = NUM_TOP_LEFT_WIDTH + 2 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.ad_area_path + time[3] + '.png')
        w = NUM_TOP_LEFT_WIDTH + 3 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        w1 = NUM_TOP_LEFT_WIDTH + 4 * IMG_NUM_WIDTH + IMG_COLON_WIDTH
        img[h:h1, w:w1] = cv2.imread(self.ad_area_path + time[4] + '.png')

        return True, img

    def start(self):
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.driver.implicitly_wait(30) #Webcat may start slowly, so set waiting time to be long
        self.driver.find_element_by_name(u"通讯录").click()
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_name(u"公众号").click()
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_name(self.webcat_account).click()
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_id('com.tencent.mm:id/fl').click()
        self.driver.implicitly_wait(10)

        ad_bottom_type, left, right = self.findAdArea(self.screen_width / 2, self.screen_height * 3 / 4, self.screen_width / 2,
                        self.screen_height / 4)
        print "bottom type:%d" %(ad_bottom_type)

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
            print "Should shrink ad area"
            #  Calculate ad area
            left = (0, left[1] + (area_height - wanted_height))
            # Calculate ad top area
            crop, img_top_left, img_top_right = self.findMatched(img_gray, self.img_top)
            ad_above_height = left[1] - img_top_right[1]
            ad_above = self.findAdAbove(ad_above_height, self.screen_width / 2, self.screen_height * 2 / 5, self.screen_width / 2,
                        self.screen_height * 3/ 5)

        # ad area is smaller than wanted, should enlarge
        if area_height - wanted_height < -3:
            print "Should enlarge ad area"
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
        if 'image-text' != self.ad_type:
            img_ad = self.warterMark(self.img_paste_ad, self.img_corner_mark)
            img_ad_resize = cv2.resize(img_ad, (self.ad_width, self.ad_height))
        else:
            img_ad_resize = self.imageText(self.img_paste_ad, self.img_corner_mark, self.desc, self.doc)
        left_side = (self.screen_width-self.ad_width)/2
        img_color[left[1]:left[1]+self.ad_height, left_side:left_side+self.ad_width] = img_ad_resize

        # Add header image
        ok, img_header = self.header(self.time, self.battery, self.network)
        if ok:
            img_color[0:self.ad_header_height, 0:self.ad_header_width] = img_header

        cv2.imwrite(self.composite_ads_path + 'screenshot-ad.png', img_color)

        sleep(3)
        self.driver.quit()

if __name__ == '__main__':
    try:
        autoImg = AutoImg('16:20', 1, '车点点', 'ads/114x114-1.jpg', 'ads/corner-mark.png', 'image-text', 'wifi', '以色列特价游', '上海往返特拉维夫3500元起')
        autoImg.start()
    except Exception as e:
        print('expet:' + repr(e))