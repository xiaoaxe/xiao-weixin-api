#!/usr/bin/env python
# encoding: utf-8

"""
@description: 路径名

@version: 1.0
@author: BaoQiang
@license: Apache Licence 
@contact: mailbaoqiang@gmail.com
@site: http://www.github.com/githubao
@software: PyCharm
@file: pth.py
@time: 2017/3/28 11:36
"""

import os
from os.path import abspath, dirname
import logging

FILE_PATH = dirname(abspath(__file__)) + os.sep + 'file' + os.sep
