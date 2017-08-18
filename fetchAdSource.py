#!/usr/bin/env python3
# coding=utf-8

import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
import time

def decode_str(s):
    if not s:
        return None
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def get_mails(prefix):
    host = 'imap.exmail.qq.com'
    username = 'wangqiang@optaim.com'
    password = 'Zhiyunzhong6868'

    server = poplib.POP3(host)
    server.user(username)
    server.pass_(password)
    # 获取最新的100封邮件
    num = len(server.list()[1])
    print 'email total num:', num
    for i in range(num, num - 100, -1):
        print i
        messages = [server.retr(i) for i in range(i, i+1)]
        messages = [b'\r\n'.join(mssg[1]) for mssg in messages]
        messages = [Parser().parsestr(mssg) for mssg in messages]
        message = messages[0]
        subject = message.get('Subject')
        subject = decode_str(subject)
        print subject
        date1 = time.strptime(message.get("Date")[0:24], '%a, %d %b %Y %H:%M:%S')  # 格式化收件时间
        date2 = time.strftime("%Y-%m-%d:%H", date1)
        print date2
        #如果标题匹配
        if subject and subject[:len(prefix)] == prefix:
            value = message.get('From')
            if value:
                hdr, addr = parseaddr(value)
                name = decode_str(hdr)
                value = u'%s <%s>' % (name, addr)
            print("sender: %s" % value)
            print("header:%s" % subject)
            for part in message.walk():
                fileName = part.get_filename()
                fileName = decode_str(fileName)
                # 保存附件
                if fileName:
                    with open(fileName, 'wb') as fEx:
                        data = part.get_payload(decode=True)
                        fEx.write(data)
                        print "Has saved attachment:", fileName
            #Have loaded the related ad resource
            break
    server.quit()

if __name__ == '__main__':
    get_mails('test_email')
