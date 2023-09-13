# -*- coding:utf-8 -*-
"""
@File: 测试.py
@Time: 2020/10/16 10:42
@By: Xianzhe
"""
import json
from conf import settings

with open(settings.FILE_DIR["account_file"], "r") as f:
    print(json.load(f))
    