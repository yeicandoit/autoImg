import cv2
import urllib

if __name__ == '__main__':
    #corner = cv2.imread("ads/qsbk_ad_corner.png", cv2.IMREAD_UNCHANGED)
    #transparency = corner[0:56, 126:134]
    #corner_save = cv2.resize(transparency, (181, 97))
    #skip = cv2.imread("ads/-1_03.png", cv2.IMREAD_UNCHANGED)
    #corner_save[32:97, 0:168] = skip
    #cv2.imwrite("ok.png", corner_save)

    #bottom = cv2.imread('bottom.png')
    #bottom[6:26, 43:83] = cv2.imread("../ad_area/shuqi-theme-bottom/battery.png")
    #cv2.imwrite("bottom_new.png", bottom)

    urllib.urlretrieve("http://pic.optaim.com/picture/2017-10/150927075460626.jpg", './test.png')
