# -*- coding:utf-8 -*-
import re
import os
import json
import hashlib

from bin import log
from conf import settings
from core import main
from core import db_handler

# 获取状态码
STATUS_CODE = settings.STATUS_CODE
# 获取文件目录
FILE_DIR = settings.FILE_DIR
# 获取服务器目录
SERVER_DIR = settings.SERVER_DIR


def file_judg(funx):
    def inner(*args, **kwargs):
        """
        数据文件状态判断 装饰器
        在数据文件丢失时保证数据文件能再生
        """
        count = 0
        md5 = hashlib.md5()
        for path in SERVER_DIR.values():                # 循环判断数据文件夹是否查找
            if not os.path.isdir(path):
                os.mkdir(path)                          # 不存在新建新文件夹
        for file in FILE_DIR:
            if not os.path.isfile(FILE_DIR[file]):     # 判断数据文件是否存在
                if re.match(r"account_file$", file):
                    # 调用日志功能接口
                    log.warning(f"用户账户数据文件不存在，已丢失全部账户数据，现已重置")
                    # 提示用户账户保存文件丢失重置情况
                    print("\033[1;31mWarring！用户账户数据文件不存在，已丢失全部账户数据，现已重置\n"
                          "默认管理员账户(admin,123456)\033[0m")
                    with open(FILE_DIR[file], "w") as f_w:
                        # 为用户账户数据文件写入初始管理员账号
                        md5.update(b"123456")
                        json.dump([{
                            "username": "admin",
                            "pwd": md5.hexdigest(),
                            "status": True,
                            "size": True
                        }], f_w)
                    db_handler.File.mkdir_home("admin")
                else:
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
        while True:
            print("\n", cls.help())
            enter = input("请输入对应选项>:").strip()
            if enter:
                if re.match(r"1$|启动服务端$", enter):
                    print("\033[1;32m服务端启动成功\033[0m\n"
                          ">>>>>>服务端行中🚩🚗 🚗 🚗 🚗 🚗 🚗")
                    cls.run_server()
                elif re.match(r"2$|查看所有用户信息$", enter):
                    cls.look_account()
                elif re.match(r"3$|创建用户$", enter):
                    ret_status = cls.save_account()
                    cls.__status_out(data=ret_status)                          # 调用打印输出
                elif re.match(r"4$|删除用户$", enter):
                    ret_status = cls.del_account()
                    cls.__status_out(data=ret_status)                          # 调用打印输出
                elif re.match(r"5$|更改用户目录总空间$", enter):
                    ret_status = cls.modify_size()
                    cls.__status_out(data=ret_status)                          # 调用打印输出
                else:
                    cls.__status_out(status_num=103)                           # 调用打印输出
            else:
                cls.__status_out(status_num=102)                               # 调用打印输出

    @staticmethod
    def help():
        """
        服务端操作帮助
        :return: 服务端帮助字符串文本
        """
        help_text = "\033[1;35m服务端操作帮助\033[0m".center(37, '=') + "\n" \
                    "| 1. \033[1;31m启动服务端是✈✈✈ \033[0m         |\n" \
                    "| 2. \033[1;32m查看所有用户信息👨 \033[0m         |\n" \
                    "| 3. \033[1;32m创建用户🤩   \033[0m             |\n" \
                    "| 4. \033[1;32m删除用户😰   \033[0m             |\n" \
                    "| 5. \033[1;32m更改用户目录总空间🍿 \033[0m       |\n" \
                    "🚗🛺🚙🚝🚅🚲🛬🛫🌌🧭🎨🕶👔🎡🎎🎋🦺"
        return help_text

    @staticmethod
    def run_server():
        """
        运行服务端
        :return: None
        """
        log.info("启动服务端")                                         # 调用日志功能接口
        server = main.TCPserver((settings.HOST, settings.PORT))      # 实例化服务端运行程序
        server.server_handle()                                       # 启动服务端

    @staticmethod
    def look_account():
        """
        查看所有用户信息
        :return: None
        """
        account_list = db_handler.Account.account_load("status")     # 调用用户信息读取
        for i in account_list:
            print(f"用户👲:\033[1;32m{i['username']}\033[0m\t"
                  f"状态🗽：\033[1;35m{i['status']}\033[0m\t"
                  f"空间容量🥚:\033[1;35m{i['size']}\033[0m")

    @classmethod
    def save_account(cls):
        """
        新建并保存用户数据
        :return: 状态码或其内容
        """
        print("\033[1;36m退出输入back或其头字母简写\033[0m")
        username = input("请输入要创建用户名(管理员账户请在用户名后面空格加-a)：").strip()
        if username:
            admin_status = False
            if re.match("back$|b$", username, flags=re.I):  # 返回判断
                return STATUS_CODE["105"]
            elif re.match(r"[\w*-/]+\s-a$", username):      # 新建管理员账户判断
                username = username.rstrip(" -a")
                admin_status = True
            elif re.match(r"[\w*-/]+$", username):          # 新建普通用户判断
                pass
            else:
                return STATUS_CODE["103"]
            pwd = input("请输入所创建用户密码：").strip()       # 输入密码
            if pwd:
                account_dic = {"username": username, "pwd": pwd}
                if admin_status:
                    # 调用日志功能接口
                    log.info(f"新建管理员账户类型,用户名: {username}")
                    # 调用用户保存功能,类型为管理员
                    ret_status = db_handler.Account.account_save(account_dic, genre="admin")
                else:
                    # 调用日志功能接口
                    log.info(f"新建管理员账户类型,用户名: {username}")
                    # 调用用户保存功能
                    ret_status = db_handler.Account.account_save(account_dic)
                return ret_status                           # 返回调用功能的返回结果
            else:
                return STATUS_CODE["102"]
        else:
            return STATUS_CODE["102"]

    @classmethod
    def del_account(cls):
        """
        删除用户(包括管理员账户)
        :return: 状态码或其内容
        """
        print("\033[1;35m删除Home目录在用户名后空格加-d\033[0m")
        username = cls.__inp()                                     # 调用敏感操作输入
        if username:
            if isinstance(username, list):
                return username
            else:
                del_status = False
                if re.match(r"[\w*-/]+\s-d$", username):               # 判断是否删除Home目录
                    username = username.rstrip(" -d")
                    del_status = True
                log.info(f"用户: {username} 账户数据删除")                # 调用日志功能接口
                ret_status = db_handler.Account.account_del(username)  # 调用删除账户功能并返回状态值
                if del_status:                                         # 判断删除Home目录是否启动
                    log.info(f"用户: {username} Home删除")               # 调用日志功能接口
                    ret_status += db_handler.File.del_home(username)   # 调用删除Home目录功能并拼接状态值
                return ret_status

    @classmethod
    def modify_size(cls):
        """
        修改用户Home目录存储大小
        :return: 状态码或其内容
        """
        username = cls.__inp()
        if isinstance(username, list):
            return username
        else:
            print("\033[1;36m空间单位现支持(TB、GB、MB、KB、B),列1GB\033[0m")
            new_size = input("请输入需要的空间大小：").strip()
            if re.match(r"\d+\s?(TB|GB|MB|KB|B)$", new_size, flags=re.I):
                log.info(f"用户: {username} Home目录大小修改为{new_size}")      # 调用日志功能接口
                ret_status = db_handler.File.home_size(username, new_size)  # 调用目录修改功能并返回状态值
                return ret_status
            else:
                return STATUS_CODE["100"]

    @staticmethod
    def __inp():
        """
        管理员操作运行输入
        :return: 状态码或其内容
        """
        while True:
            username = input("请输入用户名(取消请输入back或其简写)：").strip()
            if username:
                if re.match(r"b$|back$", username, flags=re.I):
                    return False
                else:
                    super_pwd = input("请输入超级管理员密码是🙏：").strip()
                    if super_pwd:
                        if super_pwd == settings.SUPER_PWD:
                            return username
                        else:
                            return STATUS_CODE["202"]
                    else:
                        return STATUS_CODE["102"]
            else:
                return STATUS_CODE["102"]

    @staticmethod
    def __status_out(status_num=None, data=None):
        """
        输出打印功能
        :param status_num: 传入单个状态码的码号(可传入字符串格式、整数格式)
        :param data: 传入状态码内容，可多个状态码
        :return: None
        """
        if status_num is not None:
            status = False                         # 定义输入状态
            if isinstance(status_num, str) and re.match(r"\d+", status_num):
                status = True                      # 更改状态为True
            elif isinstance(status_num, int):
                status_num = str(status_num)       # 转化整数类型为字符串
                status = True                      # 更改状态为True
            else:
                print("\033[1;32m服务端返回状态码\033[0m".center(50, ">"))
                for i in status_num:
                    if isinstance(i, int):
                        i = str(i)
                    print(f"状态码：\033[1;31m{settings.STATUS_CODE[i][0]}\033[0m "       # 格式化打印状态码内容
                          f"说明：{settings.STATUS_CODE[i][-1]}")
                print("\033[1;32m服务端返回状态码\033[0m".center(50, ">"))
            if status:
                print("\033[1;32m服务端返回状态码\033[0m".center(50, ">"))
                print(f"状态码：\033[1;31m{settings.STATUS_CODE[status_num][0]}\033[0m "  # 格式化打印状态码内容
                      f"说明：{settings.STATUS_CODE[status_num][-1]}")
                print("\033[1;32m服务端返回状态码\033[0m".center(50, ">"))

        if data is not None:
            print("\033[1;32m服务端返回状态码\033[0m".center(50, ">"))                      # 格式化打印状态码内容
            if isinstance(data[0], list):          # 判断是否嵌套元组
                for i in data:
                    print(f"状态码：\033[1;31m{i[0]}\033[0m "                             # 格式化打印状态码内容
                          f"说明：{i[-1]}")
            else:                                  # 不是嵌套直接打印
                print(f"状态码：\033[1;31m{data[0]}\033[0m "                              # 格式化打印状态码内容
                      f"说明：{data[-1]}")
            print("\033[1;32m服务端返回状态码\033[0m".center(50, ">"))




