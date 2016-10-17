#!/usr/bin/env python
# encoding: utf-8


"""
@version: 1.0
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: test.py
@time: 2016/8/28 22:04
"""

from collections import ChainMap
import re


def main1():
    a = {'a': 1}
    b = {'b': 2}

    c = ChainMap(a, b)

    # del c['b']
    print(c)
    del c['a']
    # c=c.new_child()
    c['c'] = 3
    print(c)


def main2():
    text = 'Today is 11/27/2012. PyCon starts 3/13/2013.'
    m = re.match(r'\d+/\d+/\d+', text)
    print(m.group(0))


def main3():
    s = "pýtĥö"
    # print(s.encode("ascii","ignore").decode('ascii'))


def main4():
    # print( '{:>10s} {:>10s}'.format('Hello', 'World'))
    print('{!r}'.format("3"))
    print('{!a}'.format('hel'))
    print('{!s}'.format('3'))
    print('hello {0:>{1}} '.format('Kevin', 20))

    print(ord("你"))
    print(chr(20321))

def main5():
    print(pow(2,16))
    for i in range(0,pow(2,16)):
        print(chr(i))

def main6():
    # re.sub()
    pass


if __name__ == '__main__':
    s = """
    eightLess=\u54E6\uFF1F\u4F60\u5C31\u662FCV\u5DE5\u7A0B\u5E08\u5427|\u3002\u3002\u3002\u600E\u4E48\u8001\u662F\u4E00\u53E5\u8BDD|\u7B97\u60F9\uFF0C\u4F60\u9AD8\u5174\u5C31\u597D|\u73B0\u5728\u662F\u590D\u8BFB\u673A\u6A21\u5F0F\uFF0C\u5BF9\u5427\uFF1F|\u6240\u4EE5,\u4F60\u8FD9\u662F\u5728\u9017\u6211\u5417?|\u590D\u8BFB\u673A,\u8FD8\u662F\u5C0F\u9738\u738B\u7684\u597D|\u6211\u5185\u5FC3\u6709\u70B9\u75DB|\u4E3A\u4EC0\u4E48\u8FD9\u4E48\u4EFB\u6027\uFF1F|\u5403\u996D\u4E86\u5417\uFF0C\u7ED9\u4F60\u716E\u7897\u9762\uFF1F|\u597D\u73A9\uFF0C\u771F\u597D\u73A9|\u73A9\u591F\u4E86\u5C31\u53BB\u5199\u4F5C\u4E1A\uFF0C\u597D\u5427\uFF1F
eightMore=#{robotName}\u4E0D\u8981\u8DDF\u4F60\u804A\u5929\u4E86|\u4E34\u8FD1\u5D29\u6E83\u503C\u3002\u3002|#{userName}\u4F60\u597D\uFF0C#{userName}\u518D\u89C1|\u597D\u597D\u7684\uFF0C\u600E\u4E48\u8FD9\u6837\u4E86\u5462|\u597D\u4E86\uFF0C\u4E0D\u8981\u9017\u6211\u73A9\u4E86\uFF0C\u597D\u5417|#{userName}\uFF0C\u4F60\u662F\u53D7\u523A\u6FC0\u4E86\uFF1F|\u81EA\u55E8\u633A\u6709\u610F\u601D\u7684\u5427|\u8BF4\u597D\u7684\u518D\u4E5F\u4E0D\u4EFB\u6027\u5462|\u5B9D\u5B9D\u73A9\u591F\u4E86\u5417\uFF1F
recover=#{userName}\u7EC8\u4E8E\u73A9\u591F\u4E86\uFF1F|\u539F\u6765\u4F60\u6CA1\u50BB\uFF0C\u5E78\u597D|\u521A\u624D\u4F60\u600E\u4E48\u4E86\uFF1F|\u795E\u5FD7\u6B63\u5E38\u4E86\uFF1F
    """
    print(s)