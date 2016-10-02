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
@file: mywxbot.py
@time: 2016/10/2 12:52
"""

import time
from xiaowxapi.wxapi import *

class MyWxBot(WxApi):
    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 4 and msg['content']['type']==0:
            self.send_msg_by_uid(u'hi, i received: %s' %msg, msg['user']['id'])
            self.send_img_msg_by_uid('img/1.png',msg['user']['id'])
            self.send_file_msg_by_uid('file/1.txt',msg['user']['id'])

    # def schedule(self):
    #     self.send_msg(u'tb',u'schedule')
    #     time.sleep(1)


def main():
    bot = MyWxBot()
    bot.DEBUG = True
    bot.run()


if __name__ == '__main__':
    main()

