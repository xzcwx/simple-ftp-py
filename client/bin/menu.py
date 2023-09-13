# -*- coding:utf-8 -*-

import os
import re

from bin import log
from conf import settings
from core import main

CLIENT_DIR = settings.CLIENT_DIR
FILE_DIR = settings.FILE_DIR


def file_judg(funx):
    def inner(*args, **kwargs):
        """
        数据文件状态判断 装饰器
        在数据文件丢失时保证数据文件能再生
        """
        count = 0
        for path in CLIENT_DIR.values():                # 循环判断数据文件夹是否查找
            if not os.path.isdir(path):
                os.mkdir(path)                          # 不存在新建新文件夹
        for file in FILE_DIR:
            if not os.path.isfile(FILE_DIR[file]):     # 判断数据文件是否存在
                with open(FILE_DIR[file], "w") as f_w:
                    pass                           # 新建初始空文件
                count += 1  # 数据文件不存在计数器
        if count != 0:
            # 调用日志功能接口
            log.warning(f"发现{count}个数据文件不存在，已重新创建")
            # 打印数据文件不存在数量
            print(f"\033[1;31m发现{count}个数据文件不存在，已重新创建\033[0m")
        return funx(*args, **kwargs)
    return inner


class Initial(object):
    """程序运行初始化功能类"""
    @classmethod
    @file_judg
    def handle(cls):
        """
        用户输入功能选项处理
        :return: None
        """
        print("\n", cls.help())
        enter = input("请输入对应选项>:").strip()
        if enter:
            if re.match(r"1$|启动客户端$", enter):
                print("\033[1;32m客户端启动成功\033[0m\n"
                      ">>>>>>客户端运行中🚩🚗 🚗 🚗 🚗 🚗 🚗")
                cls.run_client()

    @staticmethod
    def run_client():
        log.info("启动客户端")
        client = main.TCPclient((settings.HOST,settings.PORT))
        client.client_handle()

    @staticmethod
    def help():
        help_text = "\033[1;35m客户端操作帮助\033[0m".center(37, '=') + "\n" \
                    "| 1. \033[1;32m启动客户端✈✈✈  \033[0m         |\n" \
                    "🚗🛺🚙🚝🚅🚲🛬🛫🌌🧭🎨🕶👔🎡🎎🎋🦺"
        return help_text
