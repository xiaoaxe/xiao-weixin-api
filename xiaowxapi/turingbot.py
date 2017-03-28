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

from xiaowxapi.pth import FILE_PATH


class TuringWxBot(WxApi):
    def __init__(self):
        WxApi.__init__(self)

        self.turing_key = ""
        self.robot_switch = {}
        self.close_cnt = {}

        with open('{}/input.txt'.format(FILE_PATH), 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
            self.lines = [line.strip().split('\t') for line in self.lines]
            self.current_idx = 0

            # self.to_robot = '小冰'
            self.to_robot = '小影机器人'
            self.first_request = True

        try:
            cf = ConfigParser()
            cf.read("conf/turing.cfg")
            self.turing_key = cf.get('main', 'key')
        except Exception as e:
            pass
        logging.info('turingRobot key is : ' + self.turing_key)

    def interests_reply(self, uid, msg):
        url = 'http://127.0.0.1:5000/interests'

        body = {
            'word': msg.encode('utf-8'),
        }

        result = ''

        try:
            r = requests.post(url, data=body, timeout=10)

            if r.status_code == 200:
                json_data = json.loads(r.content.decode('unicode_escape'))
                data = json_data['data']
                if data:
                    result = '你喜欢:{{{}}}，为您推荐：{}'.format(msg, data)
        except Exception as e:
            traceback.print_exc()

        return str(result)

    # 推荐关键词列表
    def recommend_reply(self, uid, msg):
        url = 'http://127.0.0.1:5000/recommend'

        body = {
            'word': msg.encode('utf-8'),
        }
        r = requests.post(url, data=body, timeout=10)

        if r.status_code == 200:
            json_data = json.loads(r.content.decode('unicode_escape'))
            data = json_data['data']
            if not data:
                result = 'opps, no recommend'
            else:
                output = []
                for item in data:
                    output.append('{}: {}'.format(item[0], item[1]))
                result = '\n'.join(output)
        else:
            result = 'sorry, err occurred'

        return str(result)

    def word2vec_reply(self, uid, msg):
        url = 'http://127.0.0.1:5000/vec'

        body = {
            'word': msg.encode('utf-8'),
        }
        r = requests.post(url, data=body, timeout=10)

        if r.status_code == 200:
            response = json.loads(r.content.decode('unicode_escape').replace("'", '"'))
            code = response['code']
            if code != 0:
                result = response['msg']
            else:
                result = response['vec']
        else:
            result = 'sorry, err occurred.'

        return str(result)

    def turing_intelligent_reply(self, uid, msg):
        if self.turing_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = uid.replace('@', "")[:30]
            body = {
                'key': self.turing_key,
                'info': msg.encode('utf-8'),
                'userid': user_id
            }
            r = requests.post(url, data=body, timeout=10)
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
        uid = msg['user']['id']
        start_cmd = [u'开始']
        stop_cmd = [u'结束']

        # 对于每一个用户，都初始化robot_switch
        if uid not in self.robot_switch:
            self.robot_switch[uid] = False

        if self.robot_switch[uid]:
            for i in stop_cmd:
                if i == msg_data:
                    self.robot_switch[uid] = False
                    s = u'[使用"开始"开启] 机器人自动回复已关闭T_T'
                    return s
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch[uid] = True
                    s = u'[使用"结束"关闭] 机器人自动回复已开启^_^'
                    return s

        return None

    def handle_msg_all(self, msg):
        if self.first_request:
            self.send_msg(self.to_robot, 'start')
            self.first_request = False
            return None

        # 如果没有返回信息，那么现在就继续
        response = msg['content']['data']
        if not response:
            return None
        elif msg['user']['name'] != self.to_robot:
            return None
        else:
            # time.sleep(3)
            pass

        print('response: ', response)

        with open('{}\\output.txt'.format(FILE_PATH), 'a', encoding='utf-8') as fw:
            if self.uniq_msg == self.lines[self.current_idx][1]:
                fw.write('{}\t{}\n'.format('\t'.join(self.lines[self.current_idx]), response))

        # 下一条请求
        content = self.next_line()
        if content:
            self.uniq_msg = content
            self.send_msg(self.to_robot, content)
            print('request: ', content)

    def next_line(self):
        if self.current_idx < len(self.lines):
            res = self.lines[self.current_idx][1]
            self.current_idx += 1
            return res
        return None

    def schedule(self):
        # content = "你知道我是谁吗"
        # # 小冰
        # user = '小冰'
        # flag = self.send_msg(user, content)
        # # print('send flag: ', flag)
        # print('request: ', content)
        # time.sleep(1)

        pass

    def handle_msg_all_1(self, msg):
        reply = ''

        if msg['msg_type_id'] == 4:
            # reply = self.turing_intelligent_reply(msg['user']['id'], msg['content']['data'])
            # reply = self.word2vec_reply(msg['user']['id'], msg['content']['data'])
            # reply = self.recommend_reply(msg['user']['id'], msg['content']['data'])
            reply = self.interests_reply(msg['user']['id'], msg['content']['data'])

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

        logging.info('[INFO] user: ' + msg['content']['data'])
        logging.info('[INFO] robot: ' + reply)

        if reply:
            self.send_msg_by_uid(reply, msg['user']['id'])

    def handle_msg_all_2(self, msg):
        # 回复自己
        # if msg['msg_type_id'] == 4 and msg['content']['type']==0:
        #     self.switch_bot(msg)


        # if msg['msg_type_id'] == 4 and msg['content']['type'] == 0:

        uid = msg['user']['id']
        reply = ''

        if msg['msg_type_id'] == 4:
            reply = self.switch_bot(msg)
            if not reply:
                if not self.robot_switch[uid]:
                    if self.reply_cnt(uid):
                        reply = '[使用"开始""结束"控制机器人] 机器人已关闭>_<'

                elif msg['content']['type'] != 0:
                    reply = '抱歉，不支持的消息类型'
                else:
                    # reply = self.turing_intelligent_reply(msg['user']['id'], msg['content']['data'])
                    # reply = self.word2vec_reply(msg['user']['id'], msg['content']['data'])
                    reply = self.recommend_reply(msg['user']['id'], msg['content']['data'])

            # 重置计数
            if self.robot_switch[uid]:
                self.close_cnt[uid] = 0

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

        if reply:
            self.send_msg_by_uid(reply, msg['user']['id'])
            logging.info('[INFO] user: ' + msg['content']['data'])
            logging.info('[INFO] robot: ' + reply)

    def schedule_1(self):
        content = u'我很乖'

        user = u'小号'

        push = False
        hour = '22'

        if is_exact_hour(hour):
            push = True

        if push:
            if not self.send_msg_by_uid(content, dst=user):
                logging.info('[ERROR] schedule task exec failed!!!')
            time.sleep(60)

    def reply_cnt(self, uid):
        if uid not in self.close_cnt:
            self.close_cnt[uid] = 0

        if self.close_cnt[uid] is 42:
            self.close_cnt[uid] = 0

        if self.close_cnt[uid] is 0:
            self.close_cnt[uid] += 1
            return True
        else:
            self.close_cnt[uid] += 1
            return False


def is_exact_hour(h):
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
    # logging.info(isExactHour('22'))
    d = {"1": "2"}


if __name__ == '__main__':
    main()
    # test()
