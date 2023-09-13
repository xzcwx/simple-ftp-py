# -*- coding:utf-8 -*-
"""
@File: 测试.py
@Time: 2020/10/16 10:42
@By: Xianzhe
"""
import os
import json
import shelve
from conf import settings

with shelve.open(os.path.join(settings.CLIENT_DIR["temp_path"], "temp")) as f_t:
    for i in f_t:
        print(i)
        print(f_t[i])
