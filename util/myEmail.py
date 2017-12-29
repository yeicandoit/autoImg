# coding=utf-8

import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import time
import logging
logger = logging.getLogger('main.myEmail')

def decode_str(s):
    if not s:
        return None
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def get_mails(prefix, demand_day):
    host = 'imap.exmail.qq.com'
    username = 'wangqiang@optaim.com'
    password = 'Zhiyunzhong6868'

    server = poplib.POP3(host)
    server.user(username)
    server.pass_(password)
    # 获取最新的100封邮件
    num = len(server.list()[1])
    logger.debug('email total num:%d', num)
    for i in range(num, num - 100, -1):
        messages = [server.retr(i) for i in range(i, i+1)]
        messages = [b'\r\n'.join(mssg[1]) for mssg in messages]
        messages = [Parser().parsestr(mssg) for mssg in messages]
        message = messages[0]
        subject = message.get('Subject')
        subject = decode_str(subject)
        logger.debug(subject)
        date1 = time.strptime(message.get("Date")[0:24], '%a, %d %b %Y %H:%M:%S')  # 格式化收件时间
        date2 = time.strftime("%Y-%m-%d", date1)
        logger.debug(date2)
        #如果标题匹配
        if subject and subject[:len(prefix)] == prefix and date2 == demand_day:
            value = message.get('From')
            if value:
                hdr, addr = parseaddr(value)
                name = decode_str(hdr)
                value = u'%s <%s>' % (name, addr)
            logger.debug("sender: %s", value)
            logger.debug("header:%s", subject)
            for part in message.walk():
                fileName = part.get_filename()
                fileName = decode_str(fileName)
                # 保存附件
                if fileName:
                    with open(fileName, 'wb') as fEx:
                        data = part.get_payload(decode=True)
                        fEx.write(data)
                        logger.debug("Has saved attachment:%s", fileName)
                        #Have loaded the related ad resource
                        server.quit()
                        return True
    server.quit()
    return  False

def send_email(to, content='', files=None, subject="自动P图"):
    user = "wangqiang@optaim.com"
    pwd = "Zhiyunzhong6868"

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(content, 'html', 'utf-8'))

    if None != files:
        for file in files:
            part = MIMEApplication(open(file, 'rb').read())
            part.add_header('Content-Disposition', 'attachment', filename=file)
            msg.attach(part)

    s = smtplib.SMTP("smtp.exmail.qq.com", timeout=30)  # 连接smtp邮件服务器,端口默认是25
    s.login(user, pwd)  # 登陆服务器
    s.sendmail(user, to, msg.as_string())  # 发送邮件
    s.close()

if __name__ == '__main__':
    #get_mails('test_email')
    send_email("wangqiang@optaim.com", 'hellow', ["ads/4.jpg"], '自动P图-自主设置主题')
