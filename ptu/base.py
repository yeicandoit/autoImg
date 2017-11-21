#coding=utf-8
from time import sleep
from PIL import Image,ImageDraw
import cv2
import imagehash
import numpy as np
import traceback
import ConfigParser
import os
import logging
import logging.config
logging.config.fileConfig('/Users/iclick/wangqiang/autoImg/conf/log.conf')

class Base:
    TYPE_ARG = 1
    TYPE_START = 4

    def __init__(self, time, battery, img_paste_ad, img_corner_mark='ads/corner-mark.png', ad_type='banner',
                 network='wifi', desc='', doc='', doc1st_line=15, save_path='./ok.png',
                 conf='/Users/iclick/wangqiang/autoImg/conf/H60-L11.conf'):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(conf)
        self.conf = conf
        self.logger = logging.getLogger('main.autoImg')

        self.time = time
        self.battery = battery
        self.img_paste_ad = img_paste_ad
        self.img_corner_mark = img_corner_mark
        self.ad_type = ad_type
        self.network = network
        self.desc = desc
        self.doc = doc
        #TODO drop doc1st_line attribute
        self.doc1st_line = doc1st_line
        self.logger.debug("Ad demand is time:%s, battery:%f, img_past_ad:%s, img_corner_mark:%s, "
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
        self.logger.debug("Find matched area, top_left[0]:%d, top_left[1]:%d, bottom_right[0]:%d, bottom_right[1]:%d",
                     top_left[0], top_left[1], bottom_right[0], bottom_right[1])
        crop = src[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        return crop, top_left, bottom_right

    def findMatchedArea(self, src, target, fp_target):
        """ Find the matched image and its position, judge whether it is OK """
        crop, top_left, bottom_right = self.findMatched(src, target)
        fp = str(imagehash.dhash(Image.fromarray(crop)))
        self.logger.debug("Found hash is:" + fp)
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

        assert w_img >= w_mask and h_img >= h_mask, "corner_mask size is bigger than ad"

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

    def warterMarkPos(self, img, mask, pos_tl, pos_br):
        #mask = cv2.imread(corner_mark, cv2.IMREAD_UNCHANGED)
        mask_region = img[pos_tl[1]:pos_br[1], pos_tl[0]:pos_br[0]]

        alpha_channel = mask[:, :, 3]
        rgb_channels = mask[:, :, :3]
        alpha_factor = alpha_channel[:, :, np.newaxis].astype(np.float32) / 255.0
        alpha_factor = np.concatenate((alpha_factor, alpha_factor, alpha_factor), axis=2)

        front = rgb_channels.astype(np.float32) * alpha_factor
        back = mask_region.astype(np.float32) * (1 - alpha_factor)
        final_img = front + back
        img[pos_tl[1]:pos_br[1], pos_tl[0]:pos_br[0]] = final_img

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
        if 'conf/H60-L11.conf' == self.conf:
            y = self.cf.getint('battery', 'top_left_y')
            y1 = self.cf.getint('battery', 'bottom_right_y')
            x = self.cf.getint('battery', 'top_left_x')
            x1 = self.cf.getint('battery', 'bottom_right_x')
            bc_width = bc_bottom_right[0] - bc_top_left[0]
            bc_height = bc_bottom_right[1] - bc_top_left[1]
            bc_setting_width = int(bc_width * battery)
            img_bc = cv2.imread(self.cf.get(image_cf_path, 'battery_capacity'))
            img_bc = cv2.resize(img_bc, (bc_setting_width, bc_height))
            img_battery = cv2.imread(self.cf.get(image_cf_path, 'battery'))
            img_battery[bc_top_left[1]:bc_bottom_right[1], bc_top_left[0]:bc_top_left[0] + bc_setting_width] = img_bc
            img[y:y1, x:x1] = img_battery
        #elif 'conf/HTC-D316d.conf' == self.conf:
        #    img_battery = cv2.imread(self.cf.get(image_cf_path, 'battery'))
        #    img_capacity = cv2.imread(self.cf.get(image_cf_path, 'battery_capacity'))
        #    b_width = x1 -x
        #    bc_height = self.cf.getint('battery', 'capacity_height')
        #    b_height = y1 - y
        #    bc_setting_height = int(bc_height*battery)
        #    img_capacity = cv2.resize(img_capacity, (b_width, bc_setting_height))
        #    img_battery[b_height-bc_setting_height:b_height, 0:b_width] = img_capacity
        #    img[y:y1, x:x1] = img_battery

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

    def circle_new(self, img_path, bkg_path):
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
        # The circle' four corners are different, so we only use one
        radius = r2 / 2
        corner = circle.crop((0, 0, radius, radius))
        alpha.paste(corner, (0, 0))
        alpha.paste(corner.transpose(Image.ROTATE_90), (0, r2 - radius))
        alpha.paste(corner.transpose(Image.ROTATE_270), (r2 - radius, 0))
        alpha.paste(corner.transpose(Image.ROTATE_180), (r2 - radius, r2 - radius))
        ima.putalpha(alpha)
        ima.save('tmp_img/circle_new.png')
        circle_bkg = cv2.imread(bkg_path)
        cv2.imwrite('tmp_img/circle_bkg.png', cv2.resize(circle_bkg, (r2, r2)))
        return  self.warterMark('tmp_img/circle_bkg.png', 'tmp_img/circle_new.png')

    def circle_image(self, img_path):
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
        # The circle' four corners are different, so we only use one
        radius = r2 / 2
        corner = circle.crop((0, 0, radius, radius))
        alpha.paste(corner, (0, 0))
        alpha.paste(corner.transpose(Image.ROTATE_90), (0, r2 - radius))
        alpha.paste(corner.transpose(Image.ROTATE_270), (r2 - radius, 0))
        alpha.paste(corner.transpose(Image.ROTATE_180), (r2 - radius, r2 - radius))
        ima.putalpha(alpha)
        ima.save('tmp_img/circle_image.png')
        return 'tmp_img/circle_image.png'

    def circle_corder_image(self, img_path, radius=30, corders=(1,1,1,1)):
        im = Image.open(img_path).convert("RGBA")
        rad = radius  # 设置半径
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        #The circle' four corners are different, so we only use one
        corner = circle.crop((0, 0, rad, rad))
        if corders[0]:
            alpha.paste(corner, (0, 0))
        if corders[1]:
            alpha.paste(corner.transpose(Image.ROTATE_90), (0, h - rad))
        if corders[2]:
            alpha.paste(corner.transpose(Image.ROTATE_270), (w - rad, 0))
        if corders[3]:
            alpha.paste(corner.transpose(Image.ROTATE_180), (w - rad, h - rad))
        im.putalpha(alpha)
        im.save('tmp_img/circle_corder.png')
        return 'tmp_img/circle_corder.png'

    def set1stDocLen(self, doc, sec):
        cl = self.cf.getint(sec, 'doc_Chinese_width')
        el = self.cf.getint(sec, 'doc_English_width')
        fl = self.cf.getint(sec, 'doc_1stline_px_len')
        mlen = 0
        for i in range(len(doc)):
            if doc[i] <= '\u2000':
                mlen += el
            # I think Chinese and Chinese punctuation(eg:，。：) consume doc_Chinese_width length px
            else:
                mlen += cl
            if mlen > fl:
                self.logger.debug('doc first line len is:%d', i)
                return i

        return len(doc)

    def findFeedsArea(self, split, fp_split, ad_flag, fp_ad_flag, blank_height, bottom_height = 3):
        """ insert one ad between the two news.
        """
        cnt = 0
        while 1:
            cnt = cnt + 1
            assert cnt != 20, "Do not find ad area"
            try:
                try:
                    self.driver.swipe(self.screen_width / 2, self.screen_height * 3 / 4,
                                                 self.screen_width / 2, self.screen_height / 4)
                    self.driver.implicitly_wait(10)
                except:
                    pass
                sleep(0.3)
                self.driver.get_screenshot_as_file("screenshot.png")
                img = cv2.imread('screenshot.png', 0)
                ok, top_left, bottom_right = self.findMatchedArea(img, split, fp_split)
                #cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
                #cv2.imwrite("tmp_img/debug.png", img)

                if ok:
                    # Do not insert ad in page which has already had an ad
                    has_ad_flag, _, _ = self.findMatchedArea(img, ad_flag, fp_ad_flag)
                    if has_ad_flag:
                        continue
                    if self.screen_height - bottom_right[1] < blank_height + bottom_height:
                        continue
                    break
            except Exception as e:
                self.logger.error('expect:' + repr(e))

        #cv2.rectangle(img, top_left, bottom_right, (0, 0, 0), 1)
        return top_left, bottom_right

    def getImgWH(self, img):
        img_gray = cv2.imread(img, 0)
        w, h = img_gray.shape[::-1]
        return w, h

    def parseArrStr(self, tStr, sep):
        if isinstance(tStr, basestring) and isinstance(sep, basestring):
            sArr = tStr.split(sep)
            iArr = []
            for item in sArr:
                iArr.append(int(item))
            return iArr
        return []

    def run_shell(self, cmd):
        if 0 != os.system(cmd):
            self.logger.error("Execute " + cmd + " error, exit")
            exit(0)

    def clickEliment(self, device_udid, x, y):
        cmd = "adb -s %s shell input tap %d %d" % (device_udid, x, y)
        self.run_shell(cmd)
        sleep(1)

    def setHeader(self, img_color):
        # Add header image
        ok, img_header = self.header(self.time, self.battery, self.network)
        if ok:
            img_color[0:self.ad_header_height, 0:self.ad_header_width] = img_header
        return img_color

    def findElement4Awhile(self, img_element, fp_img_element, duration=10):
        cnt = 0
        while 1:
            cnt += 1
            self.driver.get_screenshot_as_file('screenshot.png')
            ok, _, _ = self.findMatchedArea(cv2.imread('screenshot.png', 0), img_element, fp_img_element)
            if ok or cnt > duration:
                break
            sleep(1)
        return ok

    def findElementPos4Awhile(self, img_element, fp_img_element, duration=10):
        cnt = 0
        while 1:
            cnt += 1
            self.driver.get_screenshot_as_file('screenshot.png')
            ok, top_left, bottom_right = self.findMatchedArea(cv2.imread('screenshot.png', 0), img_element, fp_img_element)
            if ok or cnt > duration:
                break
            sleep(1)
        return ok, top_left, bottom_right

    def start(self):
        pass

    def checkArgs(self):
        return True, None

    def compositeImage(self):
        try:
            ok, msg = self.checkArgs()
            if not ok:
                return ok, Base.TYPE_ARG, msg
            self.start()
            return True, None, None
        except Exception:
            self.logger.error(traceback.format_exc())
            if self.driver:
                self.driver.quit()
            return False, Base.TYPE_START, traceback.format_exc()

if __name__ == '__main__':
    try:
        autoImage = Base('', 1.0, '')
        autoImage.circle_corder_image('ad_area/wantu/ad_feeds_detail_.png', 4)
    except Exception as e:
        traceback.print_exc()