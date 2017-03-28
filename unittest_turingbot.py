#!/usr/bin/env python
# encoding: utf-8

"""
@description: 单独测试 回复模块的逻辑

@version: 1.0
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: unittest_turingbot.py
@time: 2017/2/19 11:03
"""

from xiaowxapi.turingbot import TuringWxBot

def tmp1():
    bot = TuringWxBot()
    res = bot.interests_reply(1,"尼玛")
    print(res)

def main():
    tmp1()


if __name__ == '__main__':
    main()

