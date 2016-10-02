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
    pass