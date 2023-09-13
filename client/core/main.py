# -*- coding:utf-8 -*-

import os
import re
import time
import json
import random
import string
import struct
import socket


from bin import log
from conf import settings
from core import db_handler


# 获取服务器IP地址
SERVER_HOST = settings.HOST
# 获取服务器端口
SERVER_PORT = settings.PORT


class TCPclient(object):
    # 客户端配置相关变量
    CODING = settings.CS_CODING
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = settings.REQUEST_QUEUE_SIZE
    allow_reuse_address = False
    max_packet_size = settings.MAX_PACKET_SIZE

    def __init__(self, client_address, connect=True):
        if isinstance(client_address, tuple):
            if len(client_address) == 2:
                self.client_address = client_address
                self.socket = socket.socket(self.address_family, self.socket_type)
                self.username = None
                if connect:
                    try:
                        self.client_connect()                                         # 调用与服务端链接
                        self.SERVER_PARAM = self.__recv_head()                        # 获取服务端发送的基本参数
                        self.MAX_LOGIN_COUNT = self.SERVER_PARAM["MAX_LOGIN_COUNT"]   # 定义最大登陆数
                        self.MAX_LOGIN_TRY = self.SERVER_PARAM["MAX_LOGIN_TRY"]       # 定义最大失败可尝试数
                        settings.TEMP_INFO = self.SERVER_PARAM["TEMP_INFO"]
                        settings.TEMP_NAME = self.SERVER_PARAM["TEMP_NAME"]
                        settings.STATUS_CODE = self.SERVER_PARAM["STATUS_CODE"]       # 定义状态码
                    except Exception:
                        # 断开与服务端链接再报错
                        self.client_close()
                        raise
            else:
                print("\033[1;31m传入元组的参数要为两个，IP地址和端口\033[0m")
        else:
            print("\033[1;31m请传入元组类型，IP地址和端口\033[0m")

    def client_handle(self):
        """输入指令处理"""
        while True:
            enter = input(">>:").strip()
            if enter:
                enter = enter.split()               # 以空格将输入指令分割为列表
                self.__client_run(enter)            # 调用指令运行
            else:
                print("\033[1;31m请不要输入空内容\033[0m")

    def client_connect(self):
        """与服务端进行链接"""
        self.socket.connect(self.client_address)
        print("\033[1;32m与服务端成功建立链接\033[0m")  # 打印链接成功提示

    def client_close(self):
        """断开链接"""
        self.socket.close()                         # 断开与服务端的链接

    def client_auth(self, user_enter):
        """
        启用用户验证登陆
        :param user_enter: 用户指令内容
        :return: None
        """
        len_head_dic = len(user_enter)                              # 获取指令长度
        if len_head_dic == 3:                                       # 判断登陆指令长度是否合规
            head_account = {"cmd": user_enter[0], "username": user_enter[1], "pwd": user_enter[-1]}
            self.__send_head(head_account)                          # 发送客户端指令
            account_dic = self.__recv_head()                        # 接受登陆指令状态
            if account_dic["status"]:                               # 指令状态为True时
                self.username = account_dic["username"]
                if account_dic["status_code"][0][0] == 206:         # 判断状态指令是否为 206(重复登陆)
                    self.__status_out(data=account_dic['status_code'][0])   # 打印状态码内容
                    while True:
                        print("是否要退出登录状态，输入(yes或首字母)确定，输入(no或首字母)取消")
                        enter = input(">>>：").strip()
                        if re.match(r"y$|yes$", enter):
                            self.client_account_out([              # 调用退出服务端登陆状态功能
                                "account_out",
                                head_account["username"],
                                head_account["pwd"]
                            ])
                            break
                        elif re.match(r"n$|no$", enter):
                            break
                        else:
                            print("\033[1;31m输入格式错误,请重新输入\033[0m")
                else:
                    print("=" * 30)                               # 用户登陆成功提示
                    print(f"|    用户:{head_account['username']} "
                          f"\033[1;32m登录成功 \033[0m")
                    print("=" * 30)
            elif account_dic["status"] is False:                  # 登陆状态为False时
                count = account_dic["status_code"][-1]            # 获取登陆失败次数
                if count > self.MAX_LOGIN_COUNT:                  # 是否大于最高可重新登陆次数
                    print("你的失败次数已超过最高上限,已被锁定,请联系管理员重试")
                elif count >= self.MAX_LOGIN_TRY:                 # 是否大于最高可尝试登陆次数
                    print(f"你已登录失败\033[1;31m{count}\033[0m次,请等待3秒后重试")
                    time.sleep(3)                                 # 休眠等待三秒
                    while True:
                        # 生成随机码
                        cdk = "".join(random.sample(string.ascii_letters + string.digits, 5))
                        print(f"输入\033[1;32m{cdk}\033[0m验证码重试")
                        enter = input("请输入验证码：").strip()
                        if enter:
                            if enter == cdk:                     # 判断输入状态码是否正确
                                print("\033[1;32m验证码验证成功\033[0m\n")
                                break
                            else:
                                print("\033[1;32m输入错误请等待3秒后重新输入\033[0m")
                                time.sleep(3)                    # 休眠等待三秒
                        else:
                            print("\033[1;31m请不要输入内容\033[0m")
                else:                                            # 其他类型直接打印状态码(一般为管理员登陆)
                    self.__status_out(data=account_dic['status_code'][0])   # 打印状态码内容
        else:
            self.__status_out(status_num=106)                    # 打印状态码内容

    def client_account_out(self, user_enter):
        """
        启用退出用户登录状态
        :param user_enter: 用户指令内容
        :return: None
        """
        self.__send_head({                         # 发送客户端指令
            "cmd": user_enter[0], 
            "username": user_enter[1], 
            "pwd": user_enter[-1]
        })
        account_out_status = self.__recv_head()    # 接受指令状态
        self.__status_out(data=account_out_status['status_code'])   # 打印状态码内容
     
    def client_get(self, user_enter):
        """
        启用从服务端传递文件到客户端(服务端上传)
        发收收
        :param user_enter: 用户指令内容
        :return: 状态码或状态内容
        """
        send_head = {                                  # 定义发送的文件信息字典
            "cmd": user_enter[0],
            "username": self.username,
            "file_name": user_enter[-1]
        }
        temp_status = self.unfinish_file()             # 调用未完成文件检测
        if temp_status != send_head["file_name"]:      # 要下载文件不能和已完成的未完成文件名冲突
            file_path = os.path.normpath(              # 获取文件路径
                os.path.join(
                    settings.CLIENT_DIR["file_path"],
                    send_head["file_name"]
                )
            )
            # 定义临时文件名
            temp_name = f"{send_head['file_name']}.{settings.TEMP_NAME}"
            # 获取临时文件路径
            temp_path = os.path.join(
                settings.CLIENT_DIR["file_path"],
                temp_name
            )
            if os.path.isfile(file_path):              # 判读文件是否存在
                return 419                             # 返回文件已存在状态码
            else:
                self.__send_head(send_head)            # 发送文件信息字典
                recv_head = self.__recv_head()         # 接收文件具体信息状态
                self.__status_out(data=recv_head["status_code"])    # 打印状态码内容
                if recv_head["status"]:                # 状态为True运行
                    file_head = recv_head["file_head"]
                    # 调用文件信息保存
                    db_handler.File.temp_file("w", file_info=file_head)
                    recv_size = 0                      # 定义文件已收取大小
                    schedule = self.__schedule_out(file_head["file_size"], 600, "g")   # 调用文件传输打印功能
                    schedule.__next__()
                    with open(temp_path, "wb") as f_w:
                        while recv_size < file_head["file_size"]:
                            recv_data = self.socket.recv(self.max_packet_size)         # 接收文件数据内容
                            f_w.write(recv_data)
                            recv_size += len(recv_data)
                            schedule.send(len(recv_data))           # 发送传输大小给文件传输打印功能
                        else:
                            self.__status_out(status_num="408")                       # 调用文件下载完成提示码
                    if file_head["file_md5"] == db_handler.File.md5_load(temp_path):  # 文件MD5值校验判断
                        os.replace(temp_path, file_path)                              # 将临时文件名替换为文件名
                        # 调用删除文件信息功能
                        ret_status = db_handler.File.temp_file("d", temp_name=temp_name)
                        self.__status_out(data=ret_status["status_code"])
                        print(f"\033[1;32m文件：{user_enter[-1]} \tMD5值："          
                              f"{file_head['file_md5']}\033[0m")
                        return 500                    # 返回校验成功状态码
                    else:
                        print(f"\033[1;31m文件：{user_enter[-1]} 文件损坏，请尝试重新下载\033[0m")
                        while True:
                            print("是(yes或其首字母)\t否(no或其首字母)")
                            del_enter = input("\033[1;30;41m是否删除损坏文件?\033[0m>>:")
                            if re.match("yes$|y$", del_enter):
                                os.remove(file_path)              # 删除损坏文件
                                return 501, 409                   # 返回校验失败、删除文件状态码
                            elif re.match("no$|n$", del_enter):
                                return 501                        # 返回校验成功状态码

    def client_put(self, user_enter):
        """
        启用从客户端传递文件到服务端(客户端上传)
        发收发
        :param user_enter: 用户指令内容
        :return: 状态码或状态内容
        """
        file_name = user_enter[-1]                                              # 获取文件名
        file_path = os.path.join(settings.CLIENT_DIR["file_path"], file_name)   # 拼接路径

        if os.path.isfile(file_path):                         # 文件是否存在
            file_size = os.path.getsize(file_path)            # 获取文件大小
            self.__send_head({                                # 发送文件具体信息状态
                "cmd": user_enter[0],
                "username": self.username,
                "file_name": file_name,
                "file_size": file_size,
                "file_md5": db_handler.File.md5_load(file_path)
            })

            recv_status = self.__recv_head()                  # 接受文件在服务端状态
            schedule = self.__schedule_out(file_size, 300, "p")  # 调用文件传输打印功能
            schedule.__next__()
            if recv_status["status"]:                         # 状态为True运行
                with open(file_path, "rb") as f_r:
                    while True:
                        send_data = f_r.read(self.max_packet_size)
                        if send_data:
                            self.socket.send(send_data)       # 发送文件数据内容
                            schedule.send(len(send_data))     # 发送传输大小给文件传输打印功能
                        else:
                            print(f"\033[1;31m文件：{file_name} 传输成功\033[0m")
                            break
            else:
                return recv_status["status_code"]            # 返回状态内容
        else:
            return 411                                       # 返回状态码

    def unfinish_file(self):
        """
        未完成下载文件判断并提示,断点续传功能实现
        :return: None
        """
        file_list = db_handler.File.ls_data(mode="f")        # 调用获取目录下所有文件名接口
        unfinish_list = []                                   # 定义未完成文件名列表

        for i in file_list:
            rule = re.match(rf".+\.{settings.TEMP_NAME}", i)
            if rule:
                unfinish_list.append(i)                      # 添加未完成文件名
        if unfinish_list:                                    # 判断未完成列表是否不为空
            status = False                                   # 输入状态
            print("\033[1;35m发现未完成下载文件\033[0m".center(40, "="))
            for i, k in enumerate(unfinish_list, 1):
                print(f" |{i}.\t\033[1;31m{k}\033[0m")
            print("="*35)

            while True:
                enter = input("请选着是否继续下载(取消输入back或其首字母简写)>>:").strip()
                if enter:
                    if re.match("back$|b$", enter, flags=re.I):
                        break
                    elif re.match(r"\d+$", enter):           # 判断是否输入数字
                        enter = int(enter) - 1               # 获取索引
                        if 0 <= enter < len(unfinish_list):
                            status = True
                            break
                        else:
                            self.__status_out(status_num=107)
                    elif enter in unfinish_list:             # 判断是否输入文件名
                        enter = unfinish_list.index(enter)   # 获取索引
                        status = True
                        break
                    else:
                        self.__status_out(status_num=103)
                else:
                    self.__status_out(status_num=102)

            if status:
                # 获取未完成文件信息
                ret_status = db_handler.File.temp_file("r", temp_name=unfinish_list[enter])
                if ret_status["status"]:
                    # 获取文件信息
                    file_info = ret_status["file_info"]
                    # 获取文件名
                    temp_name = unfinish_list[enter]
                    # 获取临时文件路径
                    temp_path = os.path.join(
                        settings.CLIENT_DIR["file_path"],
                        temp_name
                    )
                    # 获取文件路径
                    file_path = os.path.join(
                        settings.CLIENT_DIR["file_path"],
                        file_info["file_name"]
                    )
                    current_size = os.path.getsize(temp_path)   # 定义当前文件大小
                    file_info["current_size"] = current_size    # 为文件信息添加当前文件大小
                    self.__send_head({                          # 发送指令
                        "cmd": "unfinish_file",
                        "username": self.username,
                        "file_info": file_info
                    })
                    recv_status = self.__recv_head()
                    self.__status_out(data=recv_status["status_code"])
                    if recv_status["status"]:
                        # 调用文件传输打印功能
                        schedule = self.__schedule_out(file_info["file_size"], 500, "g", start_size=current_size)
                        schedule.__next__()
                        recv_size = current_size                   # 获取当前文件大小
                        with open(temp_path, "ab") as f_a:
                            while recv_size < file_info["file_size"]:
                                recv_data = self.socket.recv(self.max_packet_size)
                                f_a.write(recv_data)
                                recv_size += len(recv_data)
                                schedule.send(len(recv_data))
                            else:
                                self.__status_out(status_num=408)  # 调用文件下载完成提示码

                        if file_info["file_md5"] == db_handler.File.md5_load(temp_path):
                            os.replace(temp_path, file_path)       # 将临时文件名替换为文件名
                            ret_status = db_handler.File.temp_file("d", temp_name=temp_name)
                            self.__status_out(data=ret_status["status_code"])
                            self.__status_out(status_num=500)
                            return file_info["file_name"]
                    else:
                        self.__status_out(data=ret_status["status_code"])

    def client_text(self, head_dic):
        """测试"""
        return 500, 203

    def client_ls(self, user_enter):
        """
        启用服务端用户目录文件及文件夹展示
        :param user_enter: 用户指令内容
        :return: None
        """
        self.unfinish_file()
        self.__send_head({                        # 发送客户端指令
            "cmd": user_enter[0],
            "username": self.username
        })
        ls_data = self.__recv_head()              # 接收指令返回内容
        if ls_data["status"]:                     # 状态为True运行
            print("="*30)
            for i in ls_data["ls_dic"]:           # 格式化打印目录信息
                print(f"\033[1;32m{i}:\033[0m")
                for k in ls_data["ls_dic"][i]:
                    print(f"---- {k}")
                else:
                    print()
            return ls_data["status_code"]         # 返回状态内容
        else:
            return ls_data["status_code"]         # 返回状态内容

    def client_cd(self, user_enter):
        """
        启用服务端用户目录切换
        :param user_enter: 用户指令内容
        :return: 状态码或状态内容
        """
        if len(user_enter) == 2:
            self.__send_head({                    # 发送客户端指令
                "cmd": user_enter[0],
                "username": self.username,
                "target_dir": user_enter[-1]
            })
        elif len(user_enter) == 1:
            self.__send_head({                    # 发送客户端指令
                "cmd": user_enter[0],
                "username": self.username,
                "target_dir": None
            })
        else:
            return 106                            # 返回状态码
        cd_status = self.__recv_head()  # 接收指令返回内容
        return cd_status["status_code"]  # 返回状态内容

    def client_mkdir(self, user_enter):
        self.__send_head({                        # 发送客户端指令
            "cmd": user_enter[0],
            "username": self.username,
            "dir_name": user_enter[-1]
        })
        mkdir_status = self.__recv_head()
        self.__status_out(data=mkdir_status["status_code"])

    def client_del(self, user_enter):
        self.__send_head({                        # 发送客户端指令
            "cmd": user_enter[0],
            "username": self.username,
            "targer_dir": user_enter[-1]
        })
        del_status = self.__recv_head()           # 接收指令返回内容
        self.__status_out(data=del_status["status_code"])

    def client_help(self, user_enter):
        self.__send_head({                        # 发送客户端指令
            "cmd": user_enter[0],
        })
        help_data = self.__recv_head()            # 接收指令返回内容
        print(help_data["help_text"])

    def __client_run(self, user_enter):
        """
        根据用户输入指令与信息,调用相应的功能
        :param user_enter:
        :return:
        """
        cmd = user_enter[0]
        log.debug(f"输入指令：{' '.join(user_enter)}")                              # 调用日志功能接口
        if hasattr(self, "client_" + cmd):        # 反射运行对应功能
            func = getattr(self, "client_" + cmd)
            ret_status = func(user_enter)         # 功能函数返回的状态码或其状态内容
            if isinstance(ret_status, int) or isinstance(ret_status, str):        # 返回内容是否为整数或字符串
                self.__status_out(status_num=ret_status)                          # 调用打印状态码功能
            elif isinstance(ret_status, list):    # 返回内容是否为列表或元组
                status = True                     # 定义元组或列表内容状态
                for i in ret_status:
                    if isinstance(i, list):       # 内容是否为嵌套列表或元组
                        status = False                                            # 更改状态为False
                    elif isinstance(i, int) or i.isdigit():                       # 内容是否为整数或字符串
                        pass
                    else:
                        status = False           # 更改状态为False
                if status:
                    self.__status_out(status_num=ret_status)
                else:
                    self.__status_out(data=ret_status)
        else:
            # 如果功能指令不存在客户端,尝试直接发送给服务端
            self.__send_head({                    # 发送客户端指令
                "cmd": user_enter[0],
                "username": self.username,
                "other": user_enter[1:]
            })
            recv_data = self.__recv_head()        # 接收指令返回内容
            if "status_code" in recv_data:
                if re.match(r"205$|301$|302$", str(recv_data["status_code"][0])):
                    self.__status_out(data=recv_data["status_code"])
                else:
                    print(f"\033[1;32m服务端返回内容：{recv_data}\033[0m")
            else:
                print(f"\033[1;32m服务端返回内容：{recv_data}\033[0m")

    def __send_head(self, head_dic):
        """
        发送表头给服务端
        :param head_dic: 要发送的数据内容(字典形式)
        :return: None
        """
        head_bytes = json.dumps(head_dic).encode(self.CODING)
        head_struct = struct.pack("i", len(head_bytes))
        self.socket.send(head_struct)
        self.socket.send(head_bytes)

    def __recv_head(self):
        """
        从服务端端接受表头
        :return: 表头内容
        """
        head_size = self.socket.recv(4)
        file_head_struct = struct.unpack("i", head_size)[0]
        file_head_json = self.socket.recv(file_head_struct).decode(self.CODING)
        file_head_dic = json.loads(file_head_json)
        return file_head_dic

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

    @classmethod
    def __schedule_out(cls, file_size, freq, mode, start_size=0):
        """
        用于打印传输情况
        :param file_size: 文件大小
        :param freq: 输出间隔
        :param mode: 输出模式(上传或下载)
        :param start_size 初始传输大小,默认为0
        :return: None
        """
        status = True                           # 传入参数是否合规状态定义
        if re.match("g$|get$", mode):
            mode = "下载"
        elif re.match("p$|put$", mode):
            mode = "上传"
        else:
            status = False
        if status:                              # 参数合规运行
            count = 0                           # 循环次数计数器
            send_percent = 0                    # 发送百分比大小
            send_size = start_size              # 已发送大小
            start_time = time.time()
            while True:
                send_size += yield send_percent
                send_percent = send_size / file_size * 100
                count += 1
                if count % freq == 0:           # 打印频率判断
                    print(
                        f"\033[1;32m"
                        f"{mode}进度：{send_percent:.2f}%\t"
                        f"速度：{send_size / (time.time() - start_time) / 1024 / 1024:.2f} MB/s"
                        f"\033[0m"
                    )
        else:
            cls.__status_out(status_num=100)


if __name__ == '__main__':
    print("\033[1;31m请在statr.py文件运行本程序\033[0m")
