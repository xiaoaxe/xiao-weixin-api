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

import json
from collections import ChainMap
import re
import logging
import urllib3

import time
import random


def main():
    with open('C:\\Users\\BaoQiang\\Desktop\\nature.txt', 'r', encoding='utf-8') as f, \
            open('C:\\Users\\BaoQiang\\Desktop\\2.txt', 'w', encoding='utf-8') as fw:
        for idx,line in enumerate(f,1):
            if idx % 5 == 3:
                res = line.strip()[1:].strip()

            if idx % 5 == 0:
                res2 = line.strip()[:-1]

                fw.write('{}: {}\n'.format(res,res2))

def main8():
    with open('C:\\Users\\BaoQiang\\Desktop\\contact_list.json','r',encoding='utf-8') as f,\
    open('C:\\Users\\BaoQiang\\Desktop\\2.txt','w',encoding='utf-8') as fw:
        for line in f:
            json_data = json.loads(line.strip())
            for item in json_data:
                if not 'RemarkName' in item:
                    continue

                for i in item['RemarkName'][1:]:
                    fw.write('{}\n'.format(i))

def main7():
    time.sleep(random.uniform(0.4, 1.2))


def main1():
    a = {'a': 1}
    b = {'b': 2}

    c = ChainMap(a, b)

    # del c['b']
    logging.info(c)
    del c['a']
    # c=c.new_child()
    c['c'] = 3
    logging.info(c)


def main2():
    text = 'Today is 11/27/2012. PyCon starts 3/13/2013.'
    m = re.match(r'\d+/\d+/\d+', text)
    logging.info(m.group(0))


def main3():
    s = "pýtĥö"
    # logging.info(s.encode("ascii","ignore").decode('ascii'))


def main4():
    # logging.info( '{:>10s} {:>10s}'.format('Hello', 'World'))
    logging.info('{!r}'.format("3"))
    logging.info('{!a}'.format('hel'))
    logging.info('{!s}'.format('3'))
    logging.info('hello {0:>{1}} '.format('Kevin', 20))

    logging.info(ord("你"))
    logging.info(chr(20321))


def main5():
    logging.info(pow(2, 16))
    for i in range(0, pow(2, 16)):
        logging.info(chr(i))


def main6():
    # re.sub()
    pass


if __name__ == '__main__':
    main()
