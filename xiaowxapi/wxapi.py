#!/usr/bin/env python
# encoding: utf-8


"""
@version: 1.0
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: wxapi.py
@time: 2016/8/28 22:04
"""

import html
import json
import mimetypes
import os
import random
import re
import sys
import time
import traceback
import xml.dom.minidom
from traceback import format_exc
from urllib import parse
import webbrowser
import logging

import requests
import yattag
from requests.exceptions import ConnectionError, ReadTimeout

import codecs
from pipes import quote

logging.basicConfig(level=logging.INFO)

UNKNOWN = 'unknown'
SUCCESS = '200'
SCANED = '201'
TIMEOUT = '408'


class SafeSession(requests.Session):
    def request(self, method, url,
                params=None,
                data=None,
                headers=None,
                cookies=None,
                files=None,
                auth=None,
                timeout=None,
                allow_redirects=True,
                proxies=None,
                hooks=None,
                stream=None,
                verify=None,
                cert=None,
                json=None):
        for i in range(3):
            try:
                return super(SafeSession, self).request(method, url, params, data, headers, cookies, files, auth,
                                                        timeout, allow_redirects, proxies, hooks, stream, verify, cert,
                                                        json)
            except Exception as e:
                traceback.print_stack()
                time.sleep(60)
                continue


class WxApi:
    def __init__(self):
        self.DEBUG = False
        self.uuid = ''
        self.base_url = ''
        self.redirect_uri = ''
        self.uin = ''
        self.sid = ''
        self.skey = ''
        self.pass_ticket = ''
        self.device_id = 'e' + repr(random.random())[2:17]
        self.base_request = {}
        self.sync_key_str = ''
        self.sync_key = []
        self.sync_host = ''

        self.temp_pwd = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(self.temp_pwd):
            os.makedirs(self.temp_pwd)

        self.session = SafeSession()
        # self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5'})
        # self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'})
        # self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; GT-I9300 Build/JZO54K) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 MicroMessenger/5.2.380'})
        self.session.headers.update(
                {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0'})
        self.conf = {'qr': 'png'}

        self.my_account = {}
        self.member_list = []
        # {group_id1:{},group_id2:{}...}
        self.group_members = {}
        # {'group_member':{'id':{'type':'','info':''}}}
        self.account_info = {'group_member': {}, 'normal_member': {}}

        self.contact_list = []
        self.public_list = []
        self.group_list = []
        self.special_list = []
        self.encry_chat_room_id_list = []  # 群聊的id,获取群聊成员头像

        self.file_index = 0

    @staticmethod
    def to_unicode(string, encoding='utf-8'):
        if isinstance(string, bytes):
            return string.decode(encoding)
        elif isinstance(string, str):
            return string
        else:
            raise Exception('Unknown Type')

    def get_contact(self):
        url = self.base_url + '/webwxgetcontact?pass_ticket=%sskey=%s&r=%s' \
                              % (self.pass_ticket, self.skey, int(time.time()))
        r = self.session.post(url, data='{}')
        r.encoding = 'utf-8'
        if self.DEBUG:
            with codecs.open(os.path.join(self.temp_pwd, 'contacts.json'), 'w', 'utf-8') as f:
                f.write(r.text)
        dic = json.loads(r.text)
        self.member_list = dic['MemberList']

        special_users = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail',
                         'fmessage', 'tmessage', 'qmessage', 'qqsync', 'floatbottle',
                         'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp',
                         'blogapp', 'facebookapp', 'masssendapp', 'meishiapp',
                         'feedsapp', 'voip', 'blogappweixin', 'weixin', 'brandsessionholder',
                         'weixinreminder', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c',
                         'officialaccounts', 'notification_messages', 'wxid_novlwrv3lqwv11',
                         'gh_22b87fa7cb3c', 'wxitil', 'userexperience_alarm', 'notification_messages']

        self.contact_list = []
        self.public_list = []
        self.special_list = []
        self.group_list = []

        for contact in self.member_list:
            if contact['VerifyFlag'] & 8 != 0:  # 公众号
                self.public_list.append(contact)
                self.account_info['normal_member'][contact['UserName']] = {'type': 'public', 'info': contact}
            elif contact['UserName'] in special_users:  # 特殊账号
                self.special_list.append(contact)
                self.account_info['normal_member'][contact['UserName']] = {'type': 'special', 'info': contact}
            elif contact['UserName'].find('@@') != -1:  # 群聊
                self.group_list.append(contact)
                self.account_info['normal_member'][contact['UserName']] = {'type': 'group', 'info': contact}
            elif contact['UserName'] == self.my_account['UserName']:  # 自己
                self.account_info['normal_member'][contact['UserName']] = {'type': 'self', 'info': contact}
            else:
                self.contact_list.append(contact)
                self.account_info['normal_member'][contact['UserName']] = {'type': 'contact', 'info': contact}

        self.batch_get_group_members()

        for group in self.group_members:
            for member in self.group_members[group]:
                if member['UserName'] not in self.account_info:
                    self.account_info['group_member'][member['UserName']] = {'type': 'group_member', 'info': member,
                                                                             'group': group}

        if self.DEBUG:
            with open(os.path.join(self.temp_pwd, 'contact_list.json'), 'w') as f:
                f.write(json.dumps(self.contact_list))
            with open(os.path.join(self.temp_pwd, 'special_list.json'), 'w') as f:
                f.write(json.dumps(self.special_list))
            with open(os.path.join(self.temp_pwd, 'group_list.json'), 'w') as f:
                f.write(json.dumps(self.group_list))
            with open(os.path.join(self.temp_pwd, 'public_list.json'), 'w') as f:
                f.write(json.dumps(self.public_list))
            with open(os.path.join(self.temp_pwd, 'member_list.json'), 'w') as f:
                f.write(json.dumps(self.member_list))
            with open(os.path.join(self.temp_pwd, 'group_members.json'), 'w') as f:
                f.write(json.dumps(self.group_members))
            with open(os.path.join(self.temp_pwd, 'account_info.json'), 'w') as f:
                f.write(json.dumps(self.account_info))
        return True

    def batch_get_group_members(self):
        url = self.base_url + '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.base_request,
            'Count': len(self.group_list),
            'List': [{'UserName': group['UserName'], 'EncryChatRoomId': ''} for group in self.group_list]
        }

        r = self.session.post(url, data=json.dumps(params))
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        group_members = {}
        encry_chat_room_id = {}
        for group in dic['ContactList']:
            gid = group['UserName']
            members = group['MemberList']
            group_members['gid'] = members
            encry_chat_room_id[gid] = group['EncryChatRoomId']

        self.group_members = group_members
        self.encry_chat_room_id_list = encry_chat_room_id

    def get_group_member_name(self, gid, uid):
        if gid not in self.group_members:
            return None
        group = self.group_members[gid]
        for member in group:
            if member['UserName'] == uid:
                names = {}
                if 'RemarkName' in member and member['RemarkName']:
                    names['remark_name'] = member['RemarkName']
                if 'NickName' in member and member['NickName']:
                    names['nick_name'] = member['NickName']
                if 'DisplayName' in member and member['DisplayName']:
                    names['display_name'] = member['DisplayName']
                return names

        return None

    def get_contact_info(self, uid):
        return self.account_info['normal_member'].get(uid)

    def get_group_member_info(self, uid):
        return self.account_info['group_member'].get(uid)

    def get_contact_name(self, uid):
        info = self.get_contact_info(uid)
        if info is None:
            return None
        info = info['info']
        name = {}
        if 'RemarkName' in info and info['RemarkName']:
            name['remark_name'] = info['RemarkName']
        if 'NickName' in info and info['NickName']:
            name['nick_name'] = info['NickName']
        if 'DisplayName' in info and info['DisplayName']:
            name['display_name'] = info['DisplayName']
        if len(name) == 0:
            return None
        else:
            return name

    @staticmethod
    def get_contact_prefer_name(name):
        if name is None:
            return None
        if 'remark_name' in name:
            return name['remark_name']
        if 'nick_name' in name:
            return name['nick_name']
        if 'display_name' in name:
            return name['display_name']
        return None

    @staticmethod
    def get_group_member_prefer_name(name):
        if name is None:
            return None
        if 'remark_name' in name:
            return name['remark_name']
        if 'nick_name' in name:
            return name['nick_name']
        if 'display_name' in name:
            return name['display_name']
        return None

    def get_user_type(self, wx_user_id):
        for account in self.contact_list:
            if wx_user_id == account['UserName']:
                return 'contact'

        for account in self.public_list:
            if wx_user_id == account['UserName']:
                return 'public'

        for account in self.special_list:
            if wx_user_id == account['UserName']:
                return 'special'

        for account in self.group_list:
            if wx_user_id == account['UserName']:
                return 'group'

        for account in self.group_members:
            if wx_user_id == account['UserName']:
                return 'group_member'
        return 'unknown'

    def is_contact(self, uid):
        for account in self.contact_list:
            if uid == account['UserName']:
                return True
        return False

    def is_public(self, uid):
        for account in self.public_list:
            if uid == account['UserName']:
                return True
        return False

    def is_special(self, uid):
        for account in self.special_list:
            if uid == account['UserName']:
                return True
        return False

    def handle_msg_all(self, msg):
        """
        msg_id
        msg_type_id
        user
        content
        :param msg: 收到的消息
        :return:
        """
        pass

    @staticmethod
    def proc_at_info(msg):
        if not msg:
            return '', []
        segs = msg.split(u'\u2005')
        str_msg_all = ''
        str_msg = ''
        infos = []
        if len(segs) > 1:
            for i in range(0, len(segs) - 1):
                segs[i] += u'\u2005'
                pm = re.search(u'@.*\u2005', segs[i]).group()
                if pm:
                    name = pm[1:-1]
                    string = segs[i].replace(pm, '')
                    str_msg_all += string + '@' + name + ' '
                    str_msg += string
                    if string:
                        infos.append({'type': 'str', 'value': string})
                    infos.append({'type': 'at', 'value': name})
                else:
                    infos.append({'type': 'str', 'value': segs[i]})
                    str_msg_all += segs[i]
                    str_msg += segs[i]
            str_msg_all += segs[-1]
            str_msg += segs[-1]
            infos.append({'type': 'str', 'value': segs[-1]})
        else:
            infos.append({'type': 'str', 'value': segs[-1]})
            str_msg_all = msg
            str_msg = msg

        return str_msg_all.replace(u'\u2005', ''), str_msg.replace(u'\u2005', ''), infos

    def extract_msg_content(self, msg_type_id, msg):
        """
        0: Text
        1: Location
        3: Image
        4: Voice
        5: Recommend
        6: Animation
        7: Share
         8: Video
         9: VideoCall
         10: Redraw
         11: Empty
         99: Unknown
        """
        mtype = msg['MsgType']
        content = html.unescape(msg['Content'])
        msg_id = msg['MsgId']

        msg_content = {}
        if msg_type_id == 0:
            return {'type': 11, 'data': ''}
        elif msg_type_id == 2:
            return {'type': 0, 'data': content.replace('<br/>', '\n')}
        elif msg_type_id == 3:
            sp = content.find('<br/>')
            uid = content[:sp]
            content = content[sp:]
            content = content.replace('<br/>', '')
            uid = uid[:-1]
            name = self.get_contact_prefer_name(self.get_contact_name(uid))
            if not name:
                name = self.get_group_member_prefer_name(self.get_group_member_name(msg['FromUserName'], uid))
            if not name:
                name = 'unknown'
            msg_content['user'] = {'id': uid, 'name': name}
        else:
            pass

        msg_prefix = (msg_content['user']['name'] + ':') if 'user' in msg_content else ''

        if mtype == 1:
            if content.find('http://weixin.qq.com/cgi-bin/redirectforward?args=') != -1:
                r = self.session.get(content)
                r.encoding = 'gbk'
                data = r.text
                pos = self.search_content('title', data, 'xml')
                msg_content['type'] = 1
                msg_content['data'] = pos
                msg_content['detail'] = data
                if self.DEBUG:
                    logging.info('---> %s [Location] %s' % (msg_prefix, pos))
            else:
                msg_content['type'] = 0
                if msg_type_id == 3 or (msg_type_id == 1 and msg['ToUserName'][:2] == '@@'):  # group text msg
                    msg_infos = self.proc_at_info(content)
                    str_msg_all = msg_infos[0]
                    str_msg = msg_infos[1]
                    detail = msg_infos[2]
                    msg_content['data'] = str_msg_all
                    msg_content['detail'] = detail
                    msg_content['desc'] = str_msg
                else:
                    msg_content['data'] = content
                if self.DEBUG:
                    try:
                        logging.info('---> %s [Text] %s' % (msg_prefix, msg_content['data']))
                    except:
                        logging.info('---> %s [Text] illegal text' % msg_prefix)
        elif mtype == 3:
            msg_content['type'] = 3
            msg_content['data'] = self.get_img_url(msg_id)
            # msg_content['img'] = self.session.get(msg_content['data']).content.encode('hex')
            msg_content['img'] = self.session.get(msg_content['data']).content
            if self.DEBUG:
                image = self.get_img(msg_id)
                logging.info('---> %s [Image] %s' % (msg_prefix, image))
        elif mtype == 34:
            msg_content['type'] = 4
            msg_content['data'] = self.get_voice_url(msg_id)
            # msg_content['voice'] = self.session.get(msg_content['data']).content.encode('hex')
            msg_content['voice'] = self.session.get(msg_content['data']).content
            if self.DEBUG:
                voice = self.get_voice(msg_id)
                logging.info('  %s [Voice] %s  ' % (msg_prefix, voice))
        elif mtype == 37:
            msg_content['type'] = 37
            msg_content['data'] = msg['RecommendInfo']
            if self.DEBUG:
                logging.info('---> %s [useradd] %s' % (msg_prefix, msg['RecommendInfo']['NickName']))
        elif mtype == 42:
            msg_content['type'] = 5
            info = msg['RecommendInfo']
            msg_content['data'] = {
                'nick_name': info['NickName'],
                'alias': info['Alias'],
                'province': info['Province'],
                'city': info['City'],
                'gender': ['unknown', 'famail', 'mail'][info['Sex']]
            }
            if self.DEBUG:
                logging.info('---> %s [Recommend]' % msg_prefix)
                logging.info('---> %s' '*' * 50)
                logging.info('---> |NickName: %s' % info['NickName'])
                logging.info('---> |Alias: %s' % info['Alias'])
                logging.info('---> |Location: %s %s' % (info['Province'], info['City']))
                logging.info('---> |Gender: %s' % ['unknown', 'famail', 'mail'][info['Sex']])
                logging.info('---> %s' '*' * 50)
        elif mtype == 47:
            msg_content['type'] = 6
            msg_content['data'] = self.search_content('cdnurl', content)
            if self.DEBUG:
                logging.info('---> %s [Animation] %s' % (msg_prefix, msg_content['data']))
        elif mtype == 49:
            msg_content['type'] = 7
            if msg['AppMsgType'] == 3:
                app_msg_type = 'music'
            if msg['AppMsgType'] == 5:
                app_msg_type = 'link'
            if msg['AppMsgType'] == 7:
                app_msg_type = 'weibo'
            else:
                app_msg_type = 'unknown'

            msg_content['data'] = {
                'type': app_msg_type,
                'desc': self.search_content('des', content, 'xml'),
                'url': msg['Url'],
                'from': self.search_content('appname', content, 'xml'),
                'content': msg.get('Content')
            }

            if self.DEBUG:
                logging.info('---> %s [Share] %s' % (msg_prefix, app_msg_type))
                logging.info('---> %s' '*' * 50)
                logging.info('---> |title: %s' % msg['FileName'])
                logging.info('---> |desc: %s' % self.search_content('des', content, 'xml'))
                logging.info('---> |link: %s' % msg['Url'])
                logging.info('---> |from: %s' % self.search_content('des', content, 'xml'))
                logging.info('---> |content: %s' % (msg.get('content')[:20] if msg.get('content') else 'unknown'))
                logging.info('---> %s' '*' * 50)

        elif mtype == 62:
            msg_content['type'] = 8
            msg_content['data'] = content
            if self.DEBUG:
                logging.info('---> %s [Video] please check on mobiles' % msg_prefix)

        elif mtype == 53:
            msg_content['type'] = 9
            msg_content['data'] = content
            if self.DEBUG:
                logging.info('---> %s [Video Call]' % msg_prefix)

        elif mtype == 10002:
            msg_content['type'] = 10
            msg_content['data'] = content
            if self.DEBUG:
                logging.info('---> %s [Redraw]' % msg_prefix)

        elif mtype == 10000:
            msg_content['type'] = 12
            msg_content['data'] = content
            if self.DEBUG:
                logging.info('---> [Unknown]')

        else:
            msg_content['type'] = 99
            msg_content['data'] = content
            if self.DEBUG:
                logging.info('---> %s[Unknown]' % msg_prefix)

        return msg_content

    def handle_msg(self, r):
        """
        0: init
        1 self
        2: fileHelper
        3: group
        4: contact
        5: public
        6: special
        99: unknown
        """

        for msg in r['AddMsgList']:
            user = {'id': msg['FromUserName'], 'name': 'unknown'}
            if msg['MsgType'] == 51:  # init msg
                msg_type_id = 0
                user['name'] = 'system'
            elif msg['MsgType'] == 37:
                msg_type_id = 37
                user['name'] = 'friend request'
                content = msg['Content']
                username = content[content.index('fromusername='): content.index('encryptusername')]
                logging.info(u'Friend Request')
                logging.info(u'NickName: ' + msg['RecommendInfo']['NickName'])
                logging.info(u'AppendInfo: ' + msg['RecommendInfo']['Content'])
                logging.info(u'Ticket: ' + msg['RecommendInfo']['Ticket'])
                logging.info(u'Wx Name: ' + username)
            elif msg['FromUserName'] == self.my_account['UserName']:
                msg_type_id = 1
                user['name'] = 'self'
            elif msg['ToUserName'] == 'filehelper':
                msg_type_id = 1
                user['name'] = 'file_helper'
            elif msg['FromUserName'][:2] == '@@':  # group
                msg_type_id = 3
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            elif self.is_contact(msg['FromUserName']):  # contact
                msg_type_id = 4
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            elif self.is_public(msg['FromUserName']):  # public
                msg_type_id = 5
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            elif self.is_special(msg['FromUserName']):  # special
                msg_type_id = 6
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            else:
                msg_type_id = 99
                user['name'] = 'unknown'
            user['name'] = html.unescape(user['name'])

            if self.DEBUG and msg_type_id != 0:
                logging.info(u'---> [Msg] %s' % user['name'])
            content = self.extract_msg_content(msg_type_id, msg)
            message = {
                'msg_type_id': msg_type_id,
                'msg_id': msg['MsgId'],
                'content': content,
                'to_user_id': msg['ToUserName'],
                'user': user
            }

            self.handle_msg_all(message)

    def schedule(self):
        """
        任务处理函数，在处理消息的间隙被调用
        """
        pass

    def proc_msg(self):
        if not self.test_sync_check():
            logging.info('sync check test failed !')

        while True:
            check_time = time.time()

            try:
                [retcode, selector] = self.sync_check()
                logging.debug(u'--->sync_check: retcode: [{}]; selector: [{}].'.format(retcode, selector))
                if retcode == '1101':  # 其他网页端登录了微信
                    break
                elif retcode == '0':
                    if selector == '2':  # new msg
                        r = self.sync()
                        if r is not None:
                            self.handle_msg(r)
                    elif selector == 3:  # unknown
                        r = self.sync()
                        if r is not None:
                            self.handle_msg(r)
                    elif selector == 4:  # unknown
                        r = self.sync()
                        if r is not None:
                            self.get_contact()
                    elif selector == 6:  # maybe a red packets
                        r = self.sync()
                        if r is not None:
                            self.handle_msg(r)
                    elif selector == 7:  # operate on phone
                        r = self.sync()
                        if r is not None:
                            self.handle_msg(r)
                    elif selector == '0':
                        pass
                    else:
                        if self.DEBUG:
                            logging.info(u'--->sync_check: retcode: [{}]; selector: [{}].'.format(retcode, selector))
                        r = self.sync()
                        if r is not None:
                            self.handle_msg(r)
                else:
                    if self.DEBUG:
                        logging.info(u'--->sync_check: retcode: [{}]; selector: [{}].'.format(retcode, selector))

                self.schedule()
            except Exception as e:
                logging.info('---> {ERROR] Except in proc_msg')
                logging.info(format_exc())

            check_time = time.time() - check_time
            if check_time < 0.8:
                time.sleep(1 - check_time)

    def apply_useradd_requests(self, RecommendInfo):
        url = self.base_url + "/webwxverifyuser?r=" + str(int(time.time())) + '&lang=zh_CN'
        params = {
            'BaseRequest': self.base_request,
            'Opcode': 3,
            'VerifyUserListSize': 3,
            'VerifyUserList': [{
                'Value': RecommendInfo['UserName'],
                'VerifyUserTicket': RecommendInfo['Ticket']
            }],
            'VerifyContent': '',
            'SceneListCount': 1,
            'SceneList': [33],
            'skey': self.skey
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        try:
            r = self.session.post(url, data=data, headers=headers)
        except (ConnectionError, ReadTimeout):
            return False
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def add_groupuser_to_friend_by_uid(self, uid, VerifyContent):
        if self.is_contact(uid):
            return True
        url = self.base_url + 'webwxverifyuser?r=' + str(int(time.time())) + '&lang=zh_CN'
        params = {
            'BaseRequest': self.base_request,
            'Opcode': 2,
            'VerifyUserListSize': 1,
            'VerifyUserList': [{
                'Value': uid,
                'VerifyUserTicket': ''
            }],
            'VerifyContent': VerifyContent,
            'SceneListCount': 1,
            'SceneList': [33],
            'skey': self.skey
        }
        headers = {'content-type': 'application/json;charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        try:
            r = self.session.post(url, headers=headers, data=data)
        except (ConnectionError, ReadTimeout):
            return False
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def add_friend_to_group(self, uid, group_name):
        gid = ''
        for group in self.group_list:
            if group['NickName'] == group_name:
                gid = group['UserName']
        if gid == '':
            return False
        for user in self.group_members[gid]:
            if user['UserName'] == uid:
                return True

        url = self.base_url + '/webwxupdatechatroom?fun=addmember&pass_ticket=%s' % self.pass_ticket
        params = {
            'AddMemberList': uid,
            'ChatRoomName': gid,
            'BaseRequest': self.base_request
        }
        headers = {'content-type': 'application/json;charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        try:
            r = self.session.post(url, headers=headers, data=data)
        except (ConnectionError, ReadTimeout):
            return False
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def delete_user_from_group(self, uname, gid):
        uid = ''
        for user in self.group_members[gid]:
            if user['NickName'] == uname:
                uid = user['UserName']

        if not uid:
            return False
        url = self.base_url + 'webwxupdatechatroom?fun=delmember&pass_ticket=%s' % self.pass_ticket
        params = {
            'DelMemberList': uid,
            'ChatRoomName': gid,
            'BaseRequest': self.base_request
        }
        headers = {'content-type': 'application/json;charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        try:
            r = self.session.post(url, headers=headers, data=data)
        except (ConnectionError, ReadTimeout):
            return False
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def send_msg_by_uid(self, word, dst='filehelper'):
        url = self.base_url + '/webwxsendmsg?pass_ticket=%s' % self.pass_ticket
        msg_id = str(int(time.time() * 1000)) + str(random.random())[:5].replace('.', '')
        word = self.to_unicode(word)
        params = {
            'BaseRequest': self.base_request,
            'Msg': {
                'Type': 1,
                'Content': word,
                'FromUserName': self.my_account['UserName'],
                'ToUserName': dst,
                'LocalID': msg_id,
                'ClientMsgId': msg_id
            }
        }
        headers = {'content-type': 'application/json;charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf-8')
        try:
            r = self.session.post(url, headers=headers, data=data)
        except (ConnectionError, ReadTimeout):
            return False
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def upload_media(self, fpath, is_img=False):
        if not os.path.exists(fpath):
            logging.info('---> [ERROR] File not exists.')
            return None
        url_1 = 'http://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        url_2 = 'http://file2.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        flen = str(os.path.getsize(fpath))
        ftype = mimetypes.guess_type(fpath)[0] or 'application/octet-stream'
        files = {
            'id': (None, 'WU_FILE_%s' % str(self.file_index)),
            'name': (None, os.path.basename(fpath)),
            'type': (None, ftype),
            'lastModifyDate': (None, time.strftime('%m/%d/%Y, %H:%M:%S GTM+0800 (CST)')),
            'size': (None, flen),
            'mediatype': (None, 'pic' if is_img else 'doc'),
            'uploadmediarequest': (None, json.dumps(
                    {
                        'BaseRequest': self.base_request,
                        'ClientMediaId': int(time.time()),
                        'TotalLen': flen,
                        'StartPos': 0,
                        'DataLen': flen,
                        'MediaType': 4,
                    }
            )),
            'webwx_data_ticket': (None, self.session.cookies['webwx_data_ticket']),
            'pass_ticket': (None, self.pass_ticket),
            'filename': (os.path.basename(fpath), open(fpath, 'rb'), ftype.split('/')[1]),
        }
        self.file_index += 1
        try:
            r = self.session.post(url_1, files=files)
            if json.loads(r.text)['BaseResponse']['Ret'] != 0:
                r = self.session.post(url_2, files=files)
                if json.loads(r.text)['BaseResponse']['Ret'] != 0:
                    logging.info('---> [ERROR] upload media failsure.')
                    return None
                mid = json.loads(r.text)['MediaId']
                return mid
        except (ConnectionError, ReadTimeout):
            return None

    def send_file_msg_by_uid(self, fpath, uid):
        mid = self.upload_media(fpath)
        if mid is None or not mid:
            return False
        url = self.base_url + '/webwxsendappmsg?fun=async&pass_ticket=' + self.pass_ticket
        msg_id = str(int(time.time() * 1000)) + str(random.random())[:5].replace('.', '')
        data = {
            'BaseRequest': self.base_request,
            'Msg': {
                'Type': 6,
                'Content': (
                    '<appmsg appid="wxeb7ec651dd0aefa9" sdkver=''><title>%s</title><des>'
                    '</des><action></action><type>6</type><content></content><url></url>'
                    '<lowurl></lowurl><appattach><totallen>%s</totallen><attachid>%s</attachid>'
                    '<fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>'
                    % (os.path.basename(fpath).encode('utf-8'), str(os.path.getsize(fpath)), mid,
                       fpath.split('.')[-1])).encode('utf-8'),
                'FromUserName': self.my_account['UserName'],
                'ToUserName': uid,
                'LocalID': msg_id,
                'ClientMsgId': msg_id,
            }
        }
        try:
            r = self.session.post(url, data=json.dumps(data))
            res = json.loads(r.text)
            if res['BaseResponse']['Ret'] == 0:
                return True
            else:
                return False
        except Exception as e:
            return False

    def send_img_msg_by_uid(self, fpath, uid):
        mid = self.upload_media(fpath, is_img=True)
        if mid is None:
            return False
        url = self.base_url + '/webwxsendmsgimg?fun=async&f=json'
        data = {
            'BaseRequest': self.base_request,
            'Msg': {
                'Type': 3,
                'MediaId': mid,
                'FromUserName': self.my_account['UserName'],
                'ToUserName': uid,
                'LocalID': str(time.time() * 1e7),
                'ClientMsgId': str(time.time() * 1e7),
            },
        }
        if fpath[-4,] == '.gif':
            url = self.base_url + '/webwxsendemoticon?fun=sys'
            data['Msg']['Type'] = 47
            data['Msg']['EmojiFlag'] = 2
        try:
            r = self.session.post(url, data=json.dumps(data))
            res = json.loads(r.text)
            if res['BaseResponse']['Ret'] == 0:
                return True
            else:
                return False
        except Exception as e:
            return False

    def get_user_id(self, name):
        if name == '':
            return None
        name = self.to_unicode(name)
        for contact in self.contact_list:
            if 'RemarkName' in contact and contact['RemarkName'] == name:
                return contact['UserName']
            elif 'NickName' in contact and contact['NickName'] == name:
                return contact['UserName']
            elif 'DisplayName' in contact and contact['DisplayName'] == name:
                return contact['UserName']

        for group in self.group_list:
            if 'RemarkName' in group and group['RemarkName'] == name:
                return group['UserName']
            elif 'NickName' in group and group['NickName'] == name:
                return group['UserName']
            elif 'DisplayName' in group and group['DisplayName'] == name:
                return group['UserName']

        for public in self.public_list:
            if 'RemarkName' in public and public['RemarkName'] == name:
                return public['UserName']
            elif 'NickName' in public and public['NickName'] == name:
                return public['UserName']
            elif 'DisplayName' in public and public['DisplayName'] == name:
                return public['UserName']

        return ''

    def send_msg(self, name, word, isfile=False):
        uid = self.get_user_id(name)
        if uid:
            if isfile:
                with open(word, 'r') as f:
                    result = True
                    for line in f.readlines():
                        line = line.replace('\n', '')
                        logging.info("->{} : {}".format(name, line))
                        if self.send_msg_by_uid(line, uid):
                            pass
                        else:
                            result = False
                        time.sleep(1)
                    return result
            else:
                word = self.to_unicode(word)
                if self.send_msg_by_uid(word, uid):
                    return True
                else:
                    return False
        else:
            if self.DEBUG:
                logging.info('[ERROR] This user does not exist .')
            return False

    @staticmethod
    def search_content(key, content, fmat='attr'):
        if fmat == 'attr':
            pm = re.search(key + '\s?=\s?"([^"<]+)"', content)
            if pm:
                return pm.group(1)
            elif fmat == 'xml':
                pm = re.search('<{0}([^<]+)</{0}>'.format(key), content)
                if pm:
                    return pm.group(1)
            return 'unknown'

    def run(self):
        if not self.get_uuid():
            logging.info('get qruuid err, exit')
            sys.exit(-1)

        if not self.gen_qr_code(os.path.join(self.temp_pwd, 'wxqr.jpg')):
            logging.info('get qrcode err, exit')
            sys.exit(-1)

        logging.info('[INFO] Please use WeChat to scan the QR Code. ')

        result = self.wait4login()
        if result != SUCCESS:
            logging.info('[ERROR] Web WeChat login failed. failed code = %s' % (result))

        if self.login():
            logging.info('[INFO] Web WeChat login succeed.')
        else:
            logging.info('[ERROR] Web WeChat login failed.')
            return

        if self.init():
            logging.info('[INFO] Web WeChat init succeed.')
        else:
            logging.info('[ERROR] Web WeChat init failed.')
            return

        if not self.status_notify():
            logging.info('[ERROR] run status notify err')
        self.get_contact()

        logging.info('[INFO] Get %d contacts' % len(self.contact_list))
        logging.info('[INFO] Start to process messages...')

        self.proc_msg()

    # def gen_qr_code(self, qr_file_path):
    #     # string = 'http://login.weixin.qq.com/1/' + self.uuid
    #     qr = pyqrcode.create(string)
    #     if self.conf['qr'] == 'png':
    #         qr.png(qr_file_path, scale=8)
    #         show_images(qr_file_path)
    #     elif self.conf['qr'] == 'tty':
    #         logging.info(qr.terminal(quiet_zone=1))

    def gen_qr_code(self, qr_file_path):
        succeed = self._show_images(qr_file_path)

        return succeed

    def get_uuid(self):
        url = 'https://login.wx.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()) * 1000 + random.randint(1, 999)
        }
        r = self.session.get(url, params=params)
        r.encoding = 'utf-8'
        data = r.text
        # regx = r'window.QRLogin.code = 200; window.QRLogin.uuid = "QfZ1bC4ClA==";'
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)";'
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            return code == '200'
        else:
            logging.info(data)
        return False

    def do_request(self, url):
        r = self.session.get(url)
        r.encoding = 'utf-8'
        data = r.text
        param = re.search(r'window.code=(\d+);', data)
        code = param.group(1)
        return code, data

    def wait4login(self):
        """
        http comet:
        tip = 1, 等待用户扫描二维码
        201: scaned
        408: timeout
        tip = 0, 等待用户确认登录
        200: confirmed
        """

        LOGIN_TEMPLATE = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s'
        LOGIN_TEMPLATE = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s'
        tip = 1

        try_later_secs = 1
        MAX_RETRY_TIMES = 10

        code = UNKNOWN

        retry_time = MAX_RETRY_TIMES
        while retry_time > 0:
            url = LOGIN_TEMPLATE % (tip, self.uuid, int(time.time()))
            code, data = self.do_request(url)
            if code == SCANED:
                logging.info('[INFO] Please confirm to login.')
                tip = 0
            elif code == SUCCESS:
                param = re.search(r'window.redirect_uri="(\S+?)";', data)
                redirect_uri = param.group(1) + '&fun=new'
                self.redirect_uri = redirect_uri
                self.base_url = redirect_uri[:redirect_uri.rfind('/')]
                return code
            elif code == TIMEOUT:
                logging.info('[ERROR] WeChat login timeout. retry in %s secs later...' % try_later_secs)

                tip = 1
                retry_time -= 1
                time.sleep(try_later_secs)

        return code

    def login(self):
        if len(self.redirect_uri) < 4:
            logging.info('[ERROR] Login failed due to network problem, please try again,')
            return False
        r = self.session.get(self.redirect_uri)
        r.encoding = 'utf-8'
        data = r.text
        doc = xml.dom.minidom.parseString(yattag.indent(data))
        root = doc.documentElement

        # parser = etree.XMLParser(recover=True)
        # root = etree.fromstring(data, parser=parser)

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
            if node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
            if node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
            return False
        else:
            logging.info('[INFO] get skey, sid etc succeed.')

        self.base_request = {
            'Uin': self.uin,
            'Sid': self.sid,
            'Skey': self.skey,
            'DeviceID': self.device_id,
        }
        return True

    def init(self):
        url = self.base_url + '/webwxinit?r=%i&lang=en_US&pass_ticket=%s' % (int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.base_request
        }

        r = self.session.post(url, data=json.dumps(params))
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        self.sync_key = dic['SyncKey']
        self.my_account = dic['User']
        self.sync_key_str = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val'])
                                      for keyVal in self.sync_key['List']])
        return dic['BaseResponse']['Ret'] == 0

    def status_notify(self):
        url = self.base_url + '/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % self.pass_ticket
        self.base_request['Uin'] = int(self.base_request['Uin'])
        params = {
            'BaseRequest': self.base_request,
            'Code': 3,
            'FromUserName': self.my_account['UserName'],
            'ToUserName': self.my_account['UserName'],
            'ClientMsgId': int(time.time())
        }

        r = self.session.post(url, data=json.dumps(params))
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        return dic['BaseResponse']['Ret'] == 0

    def test_sync_check(self):
        for host in ['webpush', 'webpush2']:
            self.sync_host = host

            retcode, selector = self.sync_check()
            logging.info('test_sync_check: {},{}'.format(retcode, selector))
            if retcode == '0':
                return True
            return False

    def sync_check(self):
        params = {
            'r': int(time.time()),
            'sid': self.sid,
            'uin': self.uin,
            'skey': self.skey,
            'deviceid': self.device_id,
            'synckey': self.sync_key_str,
            '_': int(time.time()),
        }
        url = 'https://' + self.sync_host + '.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck?' + parse.urlencode(params)
        # url = 'https://' + self.sync_host + '.wx2.qq.com/cgi-bin/mmwebwx-bin/synccheck?' + parse.urlencode(params)
        logging.debug('sync_check url: ' + url)

        try:
            r = self.session.get(url, timeout=60)
            r.encoding = 'utf-8'
            data = r.text
            pm = re.search(r'window.synccheck=\{retcode:"(\d+)",selector:"(\d+)"\}', data)
            retcode = pm.group(1)
            selector = pm.group(2)

            logging.debug('sync_check, ret:{} sel:{}'.format(retcode, selector))

            return [retcode, selector]
        except Exception as e:
            return [-1, -1]

    def sync(self):
        url = self.base_url + '/webwxsync?sid=%s&skey=%s&lang=en_US&pass_ticket=%s' \
                              % (self.sid, self.skey, self.pass_ticket)
        params = {
            'BaseRequest': self.base_request,
            'SyncKey': self.sync_key,
            'rr': int(time.time())
        }

        try:
            r = self.session.post(url, data=json.dumps(params), timeout=60)
            r.encoding = 'utf-8'
            dic = json.loads(r.text)
            if dic['BaseResponse']['Ret'] == 0:
                self.sync_key = dic['SyncKey']
                self.sync_key_str = '|'.join(
                        [str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.sync_key['List']])
                return dic
        except Exception as e:
            traceback.print_exc()

        if self.DEBUG:
            logging.info('[DEBUG] sync check return nothing!')

    def get_icon(self, uid, gid=None):
        "获取联系人或群聊成员头像"
        if gid is None:
            url = self.base_url + '/webwxgeticon?username=%s&skey=%s' % (uid, self.skey)
        else:
            url = self.base_url + '/webwxgeticon?username=%s&skey=%s&chatroomid=%s' % (
                uid, self.skey, self.encry_chat_room_id_list[gid])

        r = self.session.get(url)
        data = r.content
        fn = 'icon_' + uid + 'jpg'
        with open(os.path.join(self.temp_pwd, fn), 'wb') as f:
            f.write(data)
        return fn

    def get_head_img(self, uid):
        "获取群头像"
        url = self.base_url + '/webwxgetheadimg?username=%s&skey=%s' % (uid, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'head_' + uid + '.jpg'
        with open(os.path.join(self.temp_pwd, fn), 'wb') as f:
            f.write(data)
        return fn

    def get_img_url(self, msgid):
        return self.base_url + '/webwxgetmsgimg?MsgID=%s&skey=%s' % (msgid, self.skey)

    def get_voice_url(self, msgid):
        return self.base_url + '/webwxgetvoice?msgid=%s&skey=%s' % (msgid, self.skey)

    def get_img(self, msgid):
        url = self.get_img_url(msgid)
        r = self.session.get(url)
        data = r.content
        fn = 'img_' + msgid + '.jpg'
        with open(os.path.join(self.temp_pwd), 'wb') as f:
            f.write(data)
        return fn

    def get_voice(self, msgid):
        url = self.get_voice_url(msgid)
        r = self.session.get(url)
        data = r.content
        fn = 'voice_' + msgid + '.mp3'
        with open(os.path.join(self.temp_pwd), 'wb') as f:
            f.write(data)
        return fn

    def set_remarkname(self, uid, remarkname):
        url = self.base_url + 'webwxoplog?lang=zh_CN&pass_ticket=%s' % self.pass_ticket
        remarkname = self.to_unicode(remarkname)
        params = {
            'BaseRequest': self.base_request,
            'CmdId': 2,
            'RemarkName': remarkname,
            'UserName': uid
        }

        try:
            r = self.session.post(url, data=json.dumps(params), timeout=60)
            r.encoding = 'utf-8'
            dic = json.loads(r.text)
            return dic['BaseResponse']['ErrMsg']
        except Exception as e:
            return None

    def _show_images(self, filepath):
        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        params = {
            't': 'webwx',
            '_': int(time.time())
        }

        headers = {'content-type': 'image/jpeg;charset=UTF-8'}
        # data = self.session.get(url, headers=headers, data=json.dumps(params))
        r = self.session.get(url)
        QR_CODE_PATH = self._save_File(filepath, r.content)

        if sys.platform.startswith('win'):
            os.startfile(QR_CODE_PATH)
        elif sys.platform == 'darwin':
            command = 'open -a /Applications/Previews.app %s &' % quote(QR_CODE_PATH)
            os.system(command)
        elif sys.platform.startswith('Linux'):
            # logging.info('Linux or other platform, please download your qrcode img in %s' %QR_CODE_PATH)
            webbrowser.open(os.path.join(os.getcwd(), QR_CODE_PATH))
        else:
            logging.info('Linux or other platform, please download your qrcode img in %s' % QR_CODE_PATH)

        if QR_CODE_PATH:
            return True
        return False

    def _str2qr(self):
        pass

    def _save_File(self, filename, data):
        with open(filename, 'wb') as f:
            f.write(data)
            f.close()
        return filename

        # 不可用的show image 方法
        # def show_images(file_path):

        # if sys.version_info >= (3, 3):
        #         from shlex import quote
        #     else:
        #         from pipes import quote
        #
        #     if sys.platform == 'darwin':
        #         command = 'open -a /Applications/Previews.app %s &' % quote(file_path)
        #         os.system(command)
        #     else:
        #         webbrowser.open(os.path.join(os.getcwd(), "temp", file_path))


def main():
    logging.info("do sth")


if __name__ == '__main__':
    main()
