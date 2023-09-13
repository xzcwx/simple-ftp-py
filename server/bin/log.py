# -*- coding:utf-8 -*-

import logging

from conf import settings

FILE_DIR = settings.FILE_DIR


def log_info():
    log = logging.getLogger("选课系统")
    log.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s:  %(message)s")
    handler_stream = logging.StreamHandler()  # 定义控制台输出
    handler_file = logging.FileHandler(FILE_DIR["log_file"], encoding="utf-8")  # 定义文件输出
    handler_stream.setFormatter(formatter)
    handler_file.setFormatter(formatter)
    # log.addHandler(handler_stream)        # 调用控制台输出
    log.addHandler(handler_file)            # 调用文件输出
    return log


def debug(text):
    """
    自定义debug等级日志接口
    """
    if bool(text):
        log_info().debug(text)
    else:
        print("\033[1;31m请不要输入空内容\033[0m")


def info(text):
    """
    自定义info等级日志接口
    """
    if bool(text):
        log_info().info(text)
    else:
        print("\033[1;31m请不要输入空内容\033[0m")


def warning(text):
    """
    自定义warning等级日志接口
    """
    if bool(text):
        log_info().warning(text)
    else:
        print("\033[1;31m请不要输入空内容\033[0m")


def error(text):
    """
    自定义error等级日志接口
    """
    if bool(text):
        log_info().error(text)
    else:
        print("\033[1;31m请不要输入空内容\033[0m")


def critical(text):
    """
    自定义critical等级日志接口
    """
    if bool(text):
        log_info().critical(text)
    else:
        print("\033[1;31m请不要输入空内容\033[0m")