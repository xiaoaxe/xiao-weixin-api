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
        self.robot_switch = False
        self.close_cnt = 0

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
                    result = result + '[' + k['source'] + "]" + k['article'] + '\t' + k['detailurl'] + '\n'
            else:
                result = response['text'].replace('<br>', '   ')

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
                    s = u'[使用"开始"开启] 机器人自动回复已关闭T_T'
                    return s
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch = True
                    s = u'[使用"结束"关闭] 机器人自动回复已开启^_^'
                    return s

        return None

    def handle_msg_all(self, msg):
        reply = self.switch_bot(msg)

        # 回复自己
        # if msg['msg_type_id'] == 4 and msg['content']['type']==0:
        #     self.switch_bot(msg)

        # 只有个人消息的时候，才回复这个
        is_person = False
        # if msg['msg_type_id'] == 4 and msg['content']['type'] == 0:
        if msg['msg_type_id'] == 4:
            is_person = True

        if not reply:
            if is_person:
                if not self.robot_switch:
                    if self.reply_cnt():
                        reply = '[使用"开始""结束"控制机器人] 机器人已关闭>_<'
                elif msg['content']['type'] != 0 and is_person:
                    reply = '抱歉，不支持的消息类型'
                else:
                    reply = self.turing_intelligent_reply(msg['user']['id'], msg['content']['data'])

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
                        txt = '抱歉，不支持的消息类型'
                        if msg['content']['type'] == 0:
                            txt = self.turing_intelligent_reply(msg['content']['user']['id'], msg['content']['desc'])
                        reply = "@{} {}".format(src_name, txt)

        #重置计数
        if self.robot_switch:
            self.close_cnt = 0

        if reply:
            self.send_msg_by_uid(reply, msg['user']['id'])
            print('[INFO] user: ' + msg['content']['data'])
            print('[INFO] robot: ' + reply)

    def schedule(self):
        content = u'我很乖'

        user = u'小号'

        push = False
        hour = '22'

        if isExactHour(hour):
            push = True

        if push:
            if not self.send_msg_by_uid(content, dst=user):
                print('[ERROR] schedule task exec failed!!!')
            time.sleep(60)

    def reply_cnt(self):
        if self.close_cnt is 5:
            self.close_cnt = 0

        if self.close_cnt is 0:
            self.close_cnt += 1
            return True
        else:
            self.close_cnt += 1
            return False


def isExactHour(h):
    time_array = time.localtime(time.time())
    # format_time = time.strftime("%Y-%m-%d %H:%M:%S", time.time())
    hour = time.strftime("%H", time_array)
    minute = time.strftime("%M", time_array)
    second = time.strftime("%S", time_array)
    # if h ==  hour and minute =='00' and second =='00':
    if h == hour and minute == '00':
        return True
    return False


def main():
    bot = TuringWxBot()
    # bot.DEBUG = True
    bot.run()


def test():
    print(isExactHour('22'))


if __name__ == '__main__':
    main()
    # test()
