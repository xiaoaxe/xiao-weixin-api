#!/usr/bin/env python
# encoding: utf-8

"""
@description:继承wxapi接口，实现简单的自动回复

@version: 1.0
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: testbot.py
@time: 2016/10/2 12:52
"""

import time
from xiaowxapi.wxapi import *


class DefaultBot(WxApi):
    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 4 and msg['content']['type'] == 0:
            self.send_msg_by_uid(u'hi, i received: %s' % msg['content']['data'], msg['user']['id'])
            self.send_img_msg_by_uid('img/1.png', msg['user']['id'])
            self.send_file_msg_by_uid('file/1.txt', msg['user']['id'])

    def schedule(self):
        if not self.send_msg(u'小号', u'test msg'):
            logging.info('[ERROR] schedule task exec failed!!!')
        time.sleep(1)


def main():
    bot = DefaultBot()
    bot.DEBUG = True

    bot.run()


def test():
    # url = 'https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&fun=new&lang=zh_CN&_=1475388677149'
    url = 'https://login.weixin.qq.com/qrcode/wfcDA1mk6A=='
    # bot = DefaultBot()
    logging.info(requests.get(url).text)


def test2():
    # url = 'https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&fun=new&lang=zh_CN&_=1475388677149'
    url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=1rNuNCANQHqPdZqP&skey=@crypt_9db55326_60a2947061ce89b1ba81afc27fbde155&pass_ticket=kacKwq%2B8CoOX6T8KQUGYpGPmYO06gEQBdNXvkn%2Fg54H5NLeM7wFySN3BtNcVPPiJ'
    params = "{'SyncKey': {'List': [{'Val': 640579806, 'Key': 1}, {'Val': 640579965, 'Key': 2}, {'Val': 640579916, 'Key': 3}, {'Val': 1475381161, 'Key': 1000}], 'Count': 4}, 'BaseRequest': {'Skey': '@crypt_9db55326_60a2947061ce89b1ba81afc27fbde155', 'Sid': '1rNuNCANQHqPdZqP', 'DeviceID': 'e451947568286834', 'Uin': 2491682624}, 'rr': 1475402930}"

    # logging.info(requests.post(url,params).text)

    # url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=2xYX22XMjDQi0PC7&skey=@crypt_9db55326_e39450380edc077767efad6fdcb2c391&pass_ticket=DVesc5THA0F0Yb24aKrsElU3g%252FpPm60Hk1HebPqsgzaRm8hdqoMx3M2mA15RoDTq'
    logging.info(requests.post(url, params).text)


def test3():
    a = 'ni你'
    b = u'hi, i received: %s' % a
    if isinstance(b, str):
        b = str.encode(b, 'utf-8')
    elif isinstance(b, bytes):
        b = bytes

    c = b.encode()

if __name__ == '__main__':
    main()
    # test()
    # test2()
    # test3()
