#coding=utf-8
import os
import time
import random
import logging
import logging.config

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')

path_hash = {
    'wechat_banner':u"/Volumes/Ads_Group/HuaDong/02A新点位当天素材收集/iPhone/%s/微信/582-166",
    'wechat_image_text':u"/Volumes/Ads_Group/HuaDong/02A新点位当天素材收集/iPhone/%s/微信/114-114",
    'wechat_fine_big':u"/Volumes/Ads_Group/HuaDong/02A新点位当天素材收集/iPhone/%s/微信/960-540"
}

def getImage(app, adtype):
    path_key = app + '_' + adtype
    if not path_hash.has_key(path_key):
        logger.info("path_hash does not have key:%s", path_key)
        return None

    # get image from directory today or 4days before
    for i in range(5):
        path = path_hash[path_key] % time.strftime('%Y.%m.%d', time.localtime(time.time() - i*24*60*60))
        img_list = os.listdir(path)
        if 0 == len(img_list):
            continue
        if 'Thumbs.db' in img_list:
            img_list.remove('Thumbs.db')
        img_path = path + '/' + img_list[random.randint(0, len(img_list)-1)]
        logger.info('ios image:%s', img_path)
        return img_path.encode('utf-8')

    return None

if __name__ == '__main__':
    print getImage('wechat', 'banner')


