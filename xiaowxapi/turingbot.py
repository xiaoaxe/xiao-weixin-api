#!/usr/bin/env python
# encoding: utf-8


"""
@description: 调用图灵官网api，实现的微信智能对话聊天接口

@version: 1.0
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: turingbot.py
@time: 2016/10/2 13:06
"""

from xiaowxapi.wxapi import *
from configparser import ConfigParser
import json


class TuringWxBot(WxApi):
    def __init__(self):
        WxApi.__init__(self)

        self.turing_key = ""
        self.robot_switch = True

        try:
            cf = ConfigParser()
            cf.read("conf/turing.cfg")
            self.turing_key = cf.get('main', 'key')
        except Exception as e:
            pass
        print('turingRobot key is : ' + self.turing_key)

    def turing_intelligent_reply(self, uid, msg):
        if self.turing_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = uid.replace('@', "")[:30]
            body = {
                'key': self.turing_key,
                'info': msg.encode('utf-8'),
                'userid': user_id
            }
            r = requests.post(url, data=body)
            response = json.loads(r.text)
            result = ''
            if response['code'] == 100000:
                result = response['text'].replace('<br>', "   ")
            elif response['code'] == 200000:
                result = response['url']
            elif response['code'] == 302000:
                for k in response['list']:
                    result = result + '[' + k['soruce'] + "]" + k['article'] + '\t' + k['detailurl'] + '\n'
            else:
                result = response['text'].replace('<br>', '   ')

            print('robot: ' + result)

            if result:
                return result
            else:
                return u'萌萌哒~'

    def switch_bot(self, msg):
        msg_data = msg['content']['data']
        start_cmd = [u'开始']
        stop_cmd = [u'结束']

        if self.robot_switch:
            for i in stop_cmd:
                if i == msg_data:
                    self.robot_switch = False
                    self.send_msg_by_uid(u'[ROBOT] 机器人自动回复已关闭T_T', msg['to_user_id'])
                    return True
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch = True
                    self.send_msg_by_uid(u'[ROBOT] 机器人自动回复已开启^_^', msg['to_user_id'])
                    return True

        return False

    def handle_msg_all(self, msg):
        if self.switch_bot(msg):
            return

        if not self.robot_switch and msg['content']['type'] != 0:
            s = '机器人已关闭(使用"开始"或者"结束"控制机器人) 或者 不支持的消息类型'
            return s

        # 回复自己
        # if msg['msg_type_id'] == 4 and msg['content']['type']==0:
        #     self.switch_bot(msg)

        if msg['msg_type_id'] == 4 and msg['content']['type'] == 0:  # friend msg
            self.send_msg_by_uid(self.turing_intelligent_reply(msg['user''id'], msg['content']['data']),
                                 msg['user']['id'])
        elif msg['msg_type_id'] == 3 and msg['content']['type'] == 0:  # group msg
            if 'detail' in msg['content']:
                my_names = self.get_group_member_name(self.my_account['UserName'], msg['user']['id'])
                if my_names is None:
                    my_names = {}
                if 'NickName' in self.my_account and self.my_account['NickName']:
                    my_names['nickname2'] = self.my_account['NickName']
                if 'RemarkName' in self.my_account and self.my_account['RemarkName']:
                    my_names['remarkname2'] = self.my_account['RemarkName']

                is_at_me = False
                for detail in msg['content']['detail']:
                    if detail['type'] == 'at':
                        for k in my_names:
                            if my_names[k] and my_names[k] == detail['value']:
                                is_at_me = True
                                break

                if is_at_me:
                    src_name = msg['content']['user']['name']
                    txt = '不支持的消息类型'
                    if msg['content']['type'] == 0:
                        txt = self.turing_intelligent_reply(msg['content']['user']['id'], msg['content']['desc'])
                    reply = "to {} : {}".format(src_name, txt)
                    self.send_msg_by_uid(reply, msg['user']['id'])


def main():
    bot = TuringWxBot()
    bot.DEBUG = True
    # bot.conf['qr'] = 'tty'

    bot.run()


if __name__ == '__main__':
    main()
