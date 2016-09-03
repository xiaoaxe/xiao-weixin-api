#!/usr/bin/env python
# encoding: utf-8


"""
@version: ??
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: wxapi.py
@time: 2016/8/28 22:04
"""

import os
import sys
import webbrowser
import requests
import traceback
import random
import time
import json
import re
import HTMLParser
from traceback import format_exc

UNKNOWN = 'unknown'
SUCCESS = '200'
SCANED = '201'
TIMEOUT = '408'


def show_images(file_path):
    if sys.version_info >= (3, 3):
        from shlex import quote
    else:
        from pipes import quote

    if sys.platform == 'darwin':
        command = 'open -a /Applications/Previews.app %s &' % quote(file_path)
        os.system(command)
    else:
        webbrowser.open(os.path.join(os.getcwd(), "temp", file_path))


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
                return super(SafeSession, self).request(method.url, params, data, headers, cookies, files, auth,
                                                        timeout, allow_redirects, proxies, hooks, stream, verify, cert,
                                                        json)
            except Exception as e:
                print(e, traceback.format_exc())
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
        self.base_request = ''
        self.sync_key_str = ''
        self.sync_key = ''
        self.sync_host = ''

        self.temp_pwd = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(self.temp_pwd):
            os.makedirs(self.temp_pwd)

        self.session = SafeSession()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5'})
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
        if isinstance(string, str):
            return str.encode(string, encoding)
        elif isinstance(string, bytes):
            return bytes.decode(string, encoding)
        else:
            raise Exception('Unknown Type')

    def get_contact(self):
        url = self.base_url + '/webwxgetcontact?pass_ticket=%sskey=%s&r=%s' \
                              % (self.pass_ticket, self.skey, int(time.time()))
        r = self.session.post(url, data='{}')
        r.encoding = 'utf-8'
        if self.DEBUG:
            with open(os.path.join(self.temp_pwd, 'contacts.json'), 'w') as f:
                f.write(r.text.encode('utf-8'))
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
        encry_chat_root_id = {}
        for group in dic['ContactList']:
            gid = group['UserName']
            members = group['MemberList']
            group_members['gid'] = members
            encry_chat_root_id[gid] = group['EncryChatRootId']

        self.group_members = group_members
        self.encry_chat_room_id_list = encry_chat_root_id

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
        for account in self.public_list:
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
        content = HTMLParser.HTMLParser().unescape(msg['Content'])
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
                    print('---> %s [Location] %s' % (msg_prefix, pos))
            else:
                msg_content['type'] = 0
                if msg_type_id == 3 or (msg_type_id == 1 and msg['ToUserName'][:2] == '@@'):  # group text msg
                    msg_infos = self.proc_at_info(content)
                    str_msg_all = msg_infos[content]
                    str_msg = msg_infos[1]
                    detail = msg_infos[2]
                    msg_content['data'] = str_msg_all
                    msg_content['detail'] = detail
                    msg_content['desc'] = str_msg
                else:
                    msg_content['data'] = content
                if self.DEBUG:
                    try:
                        print('---> %s [Text] %s' % (msg_prefix, msg_content['data']))
                    except:
                        print('---> %s [Text] illegal text' % msg_prefix)
        elif mtype == 3:
            msg_content['type'] = 3
            msg_content['data'] = self.get_img_url(msg_id)
            msg_content['img'] = self.session.get(msg_content['data']).content.encode('hex')
            if self.DEBUG:
                image = self.get_img(msg_id)
                print('---> %s [Image] %s' % (msg_prefix, image))
        elif mtype == 34:
            msg_content['type'] = 4
            msg_content['data'] = self.get_voice_url(msg_id)
            msg_content['voice'] = self.session.get(msg_content['data']).content.encode('hex')
            if self.DEBUG:
                voice = self.get_voice(msg_id)
                print('  %s [Voice] %s  ' % (msg_prefix, voice))
        elif mtype == 37:
            msg_content['type'] = 37
            msg_content['data'] = msg['RecommendInfo']
            if self.DEBUG:
                print('---> %s [useradd] %s' % (msg_prefix, msg['RecommendInfo']['NickName']))
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
                print('---> %s [Recommend]' % msg_prefix)
                print('---> %s' '*' * 50)
                print('---> |NickName: %s' % info['NickName'])
                print('---> |Alias: %s' % info['Alias'])
                print('---> |Location: %s %s' % (info['Province'], info['City']))
                print('---> |Gender: %s' % ['unknown', 'famail', 'mail'][info['Sex']])
                print('---> %s' '*' * 50)
        elif mtype == 47:
            msg_content['type'] = 6
            msg_content['data'] = self.search_content('cdnurl', content)
            if self.DEBUG:
                print('---> %s [Animation] %s' % (msg_prefix, msg_content['data']))
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
                print('---> %s [Share] %s' % (msg_prefix, app_msg_type))
                print('---> %s' '*' * 50)
                print('---> |title: %s' % msg['FileName'])
                print('---> |desc: %s' % self.search_content('des', content, 'xml'))
                print('---> |link: %s' % msg['Url'])
                print('---> |from: %s' % self.search_content('des', content, 'xml'))
                print('---> |content: %s' % (msg.get('content')[:20] if msg.get('content') else 'unknown'))
                print('---> %s' '*' * 50)

        elif mtype == 62:
            msg_content['type'] = 8
            msg_content['data'] = content
            if self.DEBUG:
                print('---> %s [Video] please check on mobiles' % msg_prefix)

        elif mtype == 53:
            msg_content['type'] = 9
            msg_content['data'] = content
            if self.DEBUG:
                print('---> %s [Video Call]' % msg_prefix)

        elif mtype == 10002:
            msg_content['type'] = 10
            msg_content['data'] = content
            if self.DEBUG:
                print('---> %s [Redraw]' % msg_prefix)

        elif mtype == 10000:
            msg_content['type'] = 12
            msg_content['data'] = content
            if self.DEBUG:
                print('---> [Unknown]')

        else:
            msg_content['type'] = 99
            msg_content['data'] = content
            if self.DEBUG:
                print('---> %s[Unknown]' % msg_prefix)

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
            if msg['MsgType'] == 51:
                msg_type_id = 0
                user['name'] = 'system'
            elif msg['MsgType'] == 37:
                msg_type_id = 37
                user['name'] = 'friend request'
                content = msg['Content']
                username = content[content.index('fromusername='): content.index('encryptusername')]
                print(u'Friend Request')
                print(u'NickName: ' + msg['RecommendInfo']['NickName'])
                print(u'AppendInfo: ' + msg['RecommendInfo']['Content'])
                print(u'Ticket: ' + msg['RecommendInfo']['Ticket'])
                print(u'Wx Name: ' + username)
            elif msg['FromUserName'] == self.my_account['UserName']:
                msg_type_id = 1
                user['name'] = 'self'
            elif msg['ToUserName'] == 'filehelper':
                msg_type_id = 1
                user['name'] = 'file_helper'
            elif msg['FromUserName'][:2] == '@@':
                msg_type_id = 3
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            elif self.is_contact(msg['FromUserName']):
                msg_type_id = 4
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            elif self.is_public(msg['FromUserName']):
                msg_type_id = 5
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            elif self.is_special(msg['FromUserName']):
                msg_type_id = 6
                user['name'] = self.get_contact_prefer_name(self.get_contact_name(user['id']))
            else:
                msg_type_id = 99
                user['name'] = 'unknown'
            user['name'] = HTMLParser.HTMLParser().unescape(user['name'])

            if self.DEBUG and msg_type_id != 0:
                print(u'---> [Msg] %s' % user['name'])
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
        self.test_sync_check()
        while True:
            check_time = time.time()
            try:
                [retcode, selector] = self.sync_check()
                print(u'---> sync_check: ', retcode, selector)
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
                        print(u'---> sync_check: ', retcode, selector)
                        r = self.sync()
                        if r is not None:
                            self.handle_msg(r)
                else:
                    print(u'---> sync_check: ', retcode, selector)
                self.schedule()
            except:
                print('---> {ERROR] Except in proc_msg')
                print(format_exc())

            check_time = time.time() - check_time
            if check_time > 0.8:
                time.sleep(1 - check_time)

    @staticmethod
    def search_content(key, content, fmat='attr'):
        pass

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

    def test_sync_check(self):
        pass

    def sync_check(self):
        pass

    def sync(self):
        url = self.base_url + 'webwxsync?sid=%s&skey=%s&lang=en_US&pass_ticket=%s' \
                              % (self.sid, self.skey, self.pass_ticket)
        params = {
            'BaseRequest': self.base_request,
            'SyncKey': self.sync_key,
            'rr': ~int(time.time())
        }

        try:
            r = self.session.post(url, data=json.dumps(params), timeout=60)
            r.encoding = 'utf-8'
            dic = json.loads(r.text)
            if dic['BaseResponse']['Ret'] == 0:
                self.sync_key = dic['SyncKey']
                self.sync_key_str = '|'.join([keyVal['Key'] + '_' + keyVal['Val'] for keyVal in self.sync_key['List']])
            return dic
        except Exception as e:
            return None


def main():
    print("do sth")


if __name__ == '__main__':
    main()
