#!/usr/bin/python
# -*- coding: utf8 -*-
"""
zabbix图表备份
@version: 0.1
@author: lihai
@license: Apache Licence
@contact: 13142283701 51347294@qq.com
@software: PyCharm Community Edition
@file: createReportForm.py
@time: 2016/12/27 11:12
"""

import sys

# python >3
import http.cookiejar

# python <3
"""
import cookielib.CookieJar
import urllib2
"""
import urllib
import os, datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import os, time
import logging
from logging.handlers import TimedRotatingFileHandler

# 发件人
str_from = "rgb123c@163.com"
# 收件人
list_to = ["51347294@qq.com", "keaili8@163.com"]


# 初始化发信人地址
def initListTo():
    send_path = "mail.txt"
    #print(send_path)
    send_content = open(send_path).read()
    list_to = send_content.split('|')
    return list_to


# 故障日志
"""
try:
    log_path = "log.txt"
    lines = open(log_path).readlines()
    log_content = ''
    for line in lines:
        log_content += (line.decode('gbk').encode('utf8') + "<br/>")
        # print(log_content)
except Exception, e:
    log_content = ''
"""

# zabbix 帐号&密码
username = "username"
password = "password"

# zabbix 地址
base_url = "http://100.127.112.1:8888"

# 时间段
time_interval = {
    u"1h": 3600,
    u"1d": 3600 * 24,
    u"7d": 3600 * 24 * 7
}
default_time_interval = time_interval["1d"]

# 报表参数
"""
入口总流量 1120,BGP出口流量 1466,联通流量 1415,CP流量 1114,Cache流量 1467,用户在线统计 1469
r"%s/zabbix/chart2.php?graphid=1466&period=%s"%(base_url,default_time_interval)
"""
params_config = [
    {"id": "558", "name": "入口总流量", "file_name":"input"},
    {"id": "557", "name": "综合出口总流量", "file_name":"output"},
    {"id": "638", "name": "Cache流量", "file_name":"cache"},
    {"id": "650", "name": "用户在线统计", "file_name":"users"},
]


# 登陆
def login():
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)
    url_login = r"%s/zabbix/index.php" % base_url
    postDict = {
        "name": username,
        "password": password,
        "autologin": 1,
        "enter": "Sign in"}
    postData = urllib.parse.urlencode(postDict).encode()
    response = opener.open(url_login, postData)
    # content=response.read()
    return opener


# 保存图片
def save_img(name, data):
    print(name)
    str_date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M")
    path_dir = r"backup/%s" % str_date
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)
    path_file = r"%s/%s" % (path_dir, name)
    # print(path_file.encode(encoding="utf-8"))
    f = open(file=path_file, mode='wb')
    f.write(data)
    f.flush()
    f.close()
    pass


# 发送邮件
def send_mail(smtp_server, port, account, password, str_from, list_to, msg):
    # print(msg.as_string())
    smtp = smtplib.SMTP()
    (code, resp) = smtp.connect(smtp_server, port)
    # print("connect", code, resp)
    (code, resp) = smtp.login(account, password)
    # print("login", code, resp)
    print(list_to)
    smtp.sendmail(str_from, list_to, msg.as_string())
    smtp.close()


# 生成邮件内容
def create_msg(opener):
    str_data = datetime.datetime.now().strftime("%Y-%m-%d")
    """
    if not os.path.exists(str_data):
        os.mkdir(str_data)
    """

    msgRoot = MIMEMultipart('related')
    str_subject = 'Zabbix日志_%s' % str_data
    msgRoot['Subject'] = str_subject
    msgRoot['From'] = str_from
    msgRoot['To'] = ",".join(list_to)

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    # msgText = MIMEText('This is the alternative plain text message.')
    # msgAlternative.attach(msgText)

    contents = ""
    contents += "<h1>%s</h1><br>" % str_subject
    contents += "<div>"
    for param in params_config:
        id = param["id"]
        name = param["name"]
        file_name=param["file_name"]
        graph_url = r"%s/zabbix/chart2.php?graphid=%s&period=%s" % (base_url, id, default_time_interval)
        # print(id, graph_url)
        response = opener.open(graph_url)
        data = response.read()
        save_img(r"%s.jpg" % file_name, data)
        msgImage = MIMEImage(data)
        msgImage.add_header('Content-ID', "<%s>" % id)
        msgRoot.attach(msgImage)
        contents += "<div><h2>%s</h2></div>" % name
        contents += "<div><img src='cid:%s'></div>" % id
        contents += "<br/>"

        # f=open("%s/%s.png"%(file_path,name),'wb')
        # f.write(data)
        # f.close()
    """
    if len(log_content) > 0:
        contents += "<div><h2>故障工单</h2></div><div>%s</div>" % log_content
    """

    contents += "</div>"
    msgText = MIMEText(contents, 'html', 'utf-8')
    msgAlternative.attach(msgText)
    msgRoot.attach(msgAlternative)
    return msgRoot


# 日志
def initLog():
    dir = 'log'
    if not os.path.exists(dir):
        os.mkdir(dir)
    path = dir + "/log"
    handler = TimedRotatingFileHandler(path,
                                       when="D",
                                       interval=1,
                                       backupCount=7)
    # 设置后缀名称，跟strftime的格式一样
    handler.suffix = "%Y%m%d-%H%M%S"
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        handlers=(handler,),
                        )


if __name__ == '__main__':
    try:
        initLog()

        logging.info('_______main_______')
        sleep_time = 60 * 30

        while True:
            date = datetime.datetime.now()
            logging.info("%s___%d"%(date.strftime("%Y-%m-%d %H:%M:%S"),date.hour))
            if date.hour == 23:
                # 截图发邮件
                logging.info('_____run start_____')
                # 初始化发信人地址
                list_to=initListTo()
                print(list_to)
                # 登录zabbix
                opener = login()
                # 创建邮件内容且保存图表至本地
                msg = create_msg(opener)
                # 发送邮件
                account = "account@163.com"
                password = "password"
                send_mail("smtp.163.com", "25", account, password, str_from, list_to, msg)
                logging.info('_____run end_____')
            time.sleep(sleep_time)
    except Exception as e:
        logging.exception("main exception %s" % str(e.args))
        print("run main exception", e)
