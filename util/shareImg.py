#coding=utf-8
import os
import time
import random
import logging
import logging.config

logging.config.fileConfig('conf/log.conf')
logger = logging.getLogger('main')

path_hash = {
    'weixin_banner':u"/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/微信/582-166",
    'weixin_image_text':u"/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/微信/114-114",
    'weixin_fine_big':u"/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/微信/960-540",
    'QQWeather':u"/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/QQ天气/582-166",
    'qnews_feeds_big':u'/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/腾讯新闻/大图',
    'qnews_feeds_small':u'/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/腾讯新闻/小图',
    'qnews_feeds_multi':u'/Volumes/HuaDong/02A新点位当天素材收集/iPhone/%s/腾讯新闻/组图',
}

def getImage(app, adtype = None):
    path_key = app
    if None != adtype and '' != adtype:
        path_key = app + '_' + adtype
    if not path_hash.has_key(path_key):
        logger.info("path_hash does not have key:%s", path_key)
        return None

    # get image from directory today or 4days before
    for i in range(30):
        path = path_hash[path_key] % time.strftime('%Y.%m.%d', time.localtime(time.time() - i*24*60*60))
        if not os.path.exists(path):
            logger.warning("path does not exist:%s", path)
            continue
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


