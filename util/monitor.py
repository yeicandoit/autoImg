#coding=utf-8
import subprocess
from time import sleep
import logging
import logging.config
import myEmail

shell_cmd = "tail -n 100 log/ptu.log | grep '^[0-9][0-9][0-9][0-9]'| tail -n 1 |awk '{print $2}' | awk -F':' '{print $2}'"
shell_cmd1 = "date +%M"

def check_log():
    logging.config.fileConfig('conf/log_monitor.conf')
    logger = logging.getLogger('main')

    while 1:
        child = subprocess.Popen(shell_cmd, shell=True, stdout=subprocess.PIPE)
        out = child.communicate()
        child1 = subprocess.Popen(shell_cmd1, shell=True, stdout=subprocess.PIPE)
        out1 = child1.communicate()
        if None!=out[1] or None!=out1[1]:
            myEmail.send_email("wangqiang@optaim.com", 'monitor ptu log failed', subject=u'自动P图-monitor ptu log failed')
            continue
        try:
            minu = int(out[0][:len(out)])
            minu1 = int(out1[0][:len(out1)])
            logger.debug("ptu log minute:%d, date +M:%d", minu, minu1)
            if abs(minu - minu1) > 3:
                myEmail.send_email("wangqiang@optaim.com", 'There is something wrong for service, please check log',
                               subject=u'自动P图-monitor ptu log')
        except:
            logger.warning("monitor ptu log failed")

        sleep(60)

if __name__ == '__main__':
    #check whether log time stamp is not changed for a long time
    #check whether image demand num is not 0 and not changed for a long time
    check_log()

