# -*- coding:utf-8 -*-
import os
import re
import time
import json
import struct
import socket

from bin import log
from conf import settings
from core import login
from core import db_handler

STATUS_CODE = settings.STATUS_CODE


class TCPserver(object):
    # 服务端相关配置
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    coding = settings.CS_CODING
    request_queue_size = settings.REQUEST_QUEUE_SIZE
    max_packet_size = settings.MAX_PACKET_SIZE
    user_status = db_handler.user_status
    allow_reuse_address = False
    conn, client_addr = None, None

    def __init__(self, address, activate=True):
        if isinstance(address, tuple):
            if len(address) == 2:
                self.server_address = address
                self.socket = socket.socket(self.address_family, self.socket_type)
                if activate:
                    try:
                        self.__server_bind()
                        self.__server_activate()
                    except Exception:
                        self.server_close()
                        raise
            else:
                print("\033[1;31m传入元组的参数要为两个，IP地址和端口\033[0m")
        else:
            print("\033[1;31m请传入元组类型，IP地址和端口\033[0m")

    def __server_bind(self):
        """绑定服务端IP与端口"""
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def __server_activate(self):
        """用户最大链接数、监听数"""
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        """关闭链接"""
        self.socket.close()

    def get_request(self):
        """获取客户端链接请求和地址"""
        return self.socket.accept()

    def server_handle(self):
        """处理客户端发来指令"""
        while True:
            self.conn, self.client_addr = self.get_request()
            server_param = {                            # 定义需要发给客户端的参数
                "MAX_LOGIN_COUNT": settings.MAX_LOGIN_COUNT,
                "MAX_LOGIN_TRY": settings.MAX_LOGIN_TRY,
                "TEMP_INFO": settings.TEMP_INFO,
                "TEMP_NAME": settings.TEMP_NAME,
                "STATUS_CODE": STATUS_CODE
            }
            print(server_param)
            self.__send_head(server_param)                      # 发送服务端参数给客户端
            while True:
                try:
                    head_dic = self.__recv_head()
                    print(f"\033[1;32m{head_dic}\033[0m")
                    if head_dic is not False:
                        if "username" in head_dic:              # 客户端发送的指令信息得包含用户名
                            self.user_status = login.user_status
                            if self.user_status["status"] and self.user_status["username"] == head_dic["username"]:
                                # 已是登录状态运行对应指令
                                self.__server_run(head_dic)
                            elif head_dic["cmd"] == "auth":     # 判断是否为登录指令
                                self.server_auth(head_dic)      # 调用登录功能
                            else:
                                self.__send_head({              # 发送未登录状态码
                                    "status": False,
                                    "status_code": STATUS_CODE["205"]
                                })
                        elif head_dic["cmd"] == "help":
                            self.__server_run(head_dic)
                        else:
                            self.__send_head(STATUS_CODE["303"])  # 发送用户名缺失状态码
                except WindowsError as err:
                    print(err)
                    break                                       # 与客户端链接断开时断开循环，很重要

    def server_auth(self, head_dic):
        """
        用户验证登陆
        :param head_dic: 客户端指令头
        :return: None
        """
        username, pwd = head_dic["username"], head_dic["pwd"]  # 获取用户名、密码
        auth_status = login.account_auth(username, pwd)
        print(auth_status)
        if re.match(r"200$|206$", str(auth_status[0][0])):
            self.__send_head({                                 # 发送登录成功状态内容
                "status": True,
                "username": username,
                "status_code": auth_status
            })
        else:
            self.__send_head({                                 # 发送登录失败状态内容
                "status": False,
                "status_code": auth_status
            })

    def server_account_out(self, head_dic):
        """
        退出用户登录状态
        :param head_dic: 客户端指令头
        :return: None
        """
        username, pwd = head_dic["username"], head_dic["pwd"]  # 定义用户名和密码
        account_out_status = login.account_out(username, pwd)  # 调用用户登出功能
        if re.match(r"207$", str(account_out_status[0])):      # 判断是否登出成功(207状态码)
            self.__send_head({                                 # 发送用户退出成功状态内容
                "status": True,
                "status_code": account_out_status
            })
        else:                                                  # 发送用户退出失败内容
            self.__send_head({
                "status": False,
                "status_code": account_out_status
            })

    def server_get(self, head_dic):
        """
        从服务端传递文件到客户端(服务端上传)
        :param head_dic: 客户端指令头
        :return: None
        """
        file_path = os.path.join(                              # 获取文件路径
            db_handler.user_status["current_dir"],
            head_dic["file_name"]
        )
        file_head = {                                          # 定义文件信息
            "file_name": head_dic["file_name"],
            "file_size": None,
            "file_md5": None,
            "file_path": None
        }
        if os.path.isfile(file_path):
            file_head["file_size"] = os.path.getsize(file_path)
            file_head["file_md5"] = db_handler.File.md5_load(file_path)
            file_head["file_path"] = db_handler.File.get_path(file_head["file_name"])
            self.__send_head({                                 # 发送文件具体信息
                "status": True,
                "status_code": STATUS_CODE["406"],
                "file_head": file_head
            })
            # 调用日志功能接口
            log.info(f"用户: {head_dic['username']} 下载文件:{head_dic['file_name']}")

            schedule = self.__schedule_out(file_head["file_size"], 500, "g")    # 调用文件传输打印功能
            schedule.__next__()
            with open(file_path, "rb") as f_r:
                while True:
                    send_data = f_r.read(self.max_packet_size)
                    if send_data:
                        self.conn.send(send_data)                       # 发送文件数据内容
                        schedule.send(len(send_data))                   # 发送传输大小给文件传输打印功能
                    else:
                        print(f"\033[1;31m文件：{head_dic['file_name']} 传输成功\033[0m")
                        break
        else:
            self.__send_head({
                "status": False,
                "status_code": [STATUS_CODE["300"], STATUS_CODE["411"]],
            })

    def server_put(self, head_dic):
        """
        从客户端传递文件到服务端(服务端下载)
        :param head_dic: 客户端指令头
        :return: None
        """
        file_info = {                                      # 获取客户端发送的文件信息
            "file_name": head_dic["file_name"],
            "file_size": head_dic["file_size"],
            "file_md5": head_dic["file_md5"]
        }
        file_path = os.path.join(                          # 获取文件目录
            db_handler.user_status["current_dir"],
            file_info["file_name"]
        )
        temp_path = os.path.join(                          # 临时下载文件路径
            db_handler.user_status["current_dir"],
            f"{file_info['file_name']}.{settings.TEMP_NAME}"
        )
        file_size_status = db_handler.File.dirsize_judg(   # 判断用户目录存储空间是否足够
            head_dic["username"],
            file_info["file_size"]
        )
        print(f"\033[1;32m{file_size_status}\033[0m")
        dir_status = False
        print(file_path)

        if os.path.isfile(file_path):         # 判断文件是否已存在
            self.__send_head({
                "status": False,
                "status_code": [STATUS_CODE["300"], STATUS_CODE["419"]]
            })
        else:
            if file_size_status:              # 用户目录存储空间是否足够
                dir_status = True
                self.__send_head({            # 发送存储状态
                    "status": True,
                    "status_code": [STATUS_CODE["300"]]
                })
            else:
                self.__send_head({            # 发送存储状态
                    "status": False,
                    "status_code": [STATUS_CODE["300"], STATUS_CODE["420"]]
                })
        if dir_status:
            # 调用日志功能接口
            log.info(f"用户:{head_dic['username']} 上传文件:{file_info['file_name']}")
            recv_size = 0
            schedule = self.__schedule_out(file_info["file_size"], 500, "g")    # 调用文件传输打印功能
            schedule.__next__()
            with open(temp_path, "wb") as f_w:
                while recv_size < file_info["file_size"]:
                    recv_data = self.conn.recv(self.max_packet_size)            # 接收文件数据内容
                    f_w.write(recv_data)
                    recv_size += len(recv_data)
                    schedule.send(len(recv_data))                               # 发送传输大小给文件传输打印功能
                else:
                    self.__status_out(status_num=408)                           # 调用文件下载完成提示码

            if db_handler.File.md5_load(temp_path) == file_info["file_md5"]:
                os.replace(temp_path, file_path)                                # 将临时文件名替换为文件名
                print(f"\033[1;32m文件：{file_info['file_name']} 校验成功 \tMD5值："
                      f"{file_info['file_md5']}\033[0m")
            else:
                os.remove(file_path)           # 客户端所上传的文件校验失败直接删除
                print(f"\033[1;32m文件：{file_info['file_name']} 校验失败 \tMD5值："
                      f"{file_info['file_md5']} \t 现已删除\033[0m")

    def server_unfinish_file(self, head_dic):
        """
         从服务端传递未完成文件数据到客户端(服务端上传)
        :param head_dic: 客户端指令头
        :return: None
        """
        file_info = head_dic["file_info"]
        print(file_info)
        file_path = os.path.realpath(os.path.join(
            settings.SERVER_DIR["account_home_path"],
            file_info["file_path"].lstrip(r"\\")
        ))
        print(file_path)
        if os.path.isfile(file_path):
            self.__send_head({
                "status": True,
                "status_code": [settings.STATUS_CODE["300"],settings.STATUS_CODE["406"]]
            })
            with open(file_path, "rb") as f_r:
                f_r.seek(file_info["current_size"])                         # 移动文件数据光标
                schedule = self.__schedule_out(os.path.getsize(file_path), 500, "g")
                schedule.__next__()
                while True:
                    send_data = f_r.read(self.max_packet_size)
                    if send_data:
                        self.conn.send(send_data)
                        schedule.send(len(send_data))
                    else:
                        print(f"\033[1;31m文件：{file_info['file_name']} 传输成功\033[0m")
                        break
        else:
            self.__send_head({
                "status": False,
                "status_code": [settings.STATUS_CODE["300"], settings.STATUS_CODE["411"]]
            })

    def server_text(self, head_dic):
        """测试"""
        self.__send_head(head_dic)

    def server_ls(self):
        """
        用户所在目录列表展示
        :return: None
        """
        ls_dic = db_handler.File.ls_data()
        if ls_dic:
            self.__send_head({                 # 发送状态与目录信息内容
                "status": True,
                "status_code": [STATUS_CODE["300"], STATUS_CODE["413"]],
                "ls_dic": ls_dic
            })
        else:
            self.__send_head({                 # 发送状态
                "status": False,
                "status_code": [STATUS_CODE["300"], STATUS_CODE["414"]]
            })

    def server_cd(self, head_dic):
        """
        用户目录切换
        :param head_dic: 客户端指令头
        :return: None
        """
        ls_dic = db_handler.File.ls_data()
        target_dir = head_dic["target_dir"]
        if ls_dic:
            if target_dir in ls_dic["文件夹"]:         # 判断文件夹名是否存在与当前目录
                new_dir = os.path.join(db_handler.user_status["current_dir"], target_dir)
                db_handler.user_status["current_dir"] = new_dir
                status = "415"          # 指定状态码
            elif target_dir is None:
                db_handler.user_status["current_dir"] = db_handler.user_status["home_dir"]
                status = "418"
            elif re.match(r"\.{2}$", target_dir):     # 判断是否为返回上级目录
                if db_handler.user_status["current_dir"] == db_handler.user_status["home_dir"]:
                    status = "417"      # 指定状态码
                else:
                    last_dir = os.path.dirname(db_handler.user_status["current_dir"])
                    db_handler.user_status["current_dir"] = last_dir
                    status = "416"
            elif re.match(r"\.$", target_dir):        # 判断是否为返回根目录
                status = "415"          # 指定状态码
            else:
                status = "414"          # 指定状态码
            self.__send_head({
                "status": True,
                "status_code": [STATUS_CODE["300"], STATUS_CODE[status]]
            })

    def server_mkdir(self, head_dic):
        """
        服务端用户目录创建文件夹
        :param head_dic: 客户端指令头
        :return: None
        """
        dir_name = head_dic["dir_name"]
        if re.match(r".+\.\w+", dir_name):                     # 判断输入是否为文件名格式
            self.__send_head({                                  # 发送格式错误状态
                "status": False,
                "status_code": STATUS_CODE["421"]
            })
        else:
            ret_status = db_handler.File.mkdir_dir(dir_name)    # 调用新建文件夹功能
            if re.match(r"410$", str(ret_status[1][0])):        # 判断是否为410状态码(创建失败)
                self.__send_head({                              # 发送创建失败状态
                    "status": False,
                    "status_code": ret_status
                })
            else:
                self.__send_head({                              # 发送创建成功状态
                    "status": True,
                    "status_code": ret_status
                })

    def server_del(self, head_dic):
        """
        删除服务端用户目录文件夹或文件
        :param head_dic: 指令头
        :return: None
        """
        target_dir = head_dic["targer_dir"]                     # 获取目标文件名或文件夹名
        ret_status = db_handler.File.del_dir(target_dir)        # 调用文件或文件夹删除功能
        if ret_status:
            self.__send_head({                                  # 发送删除成功状态
                "status": True,
                "status_code": ret_status
            })
        else:
            self.__send_head({                                  # 发送删除失败状态
                "status": False,
                "status_code": [STATUS_CODE["300"], STATUS_CODE["412"]]
            })

    def server_help(self):
        help_text = "\033[1;35mFTP程序指令操作帮助\033[0m".center(55, '=') + "\n" \
                    "| 1. \033[1;32m 指令: auth 用户名 密码     ==登录用户\033[0m         |\n" \
                    "| 2. \033[1;32m 指令: ls                 ==查看当前目录\033[0m      |\n" \
                    "| 3. \033[1;32m 指令: cd  -根目录  | cd .  -当前目录\033[0m         |\n" \
                    "|    \033[1;32m      cd ..  -上级目录     ==切换目录\033[0m         |\n" \
                    "| 4. \033[1;32m 指令: mkdir 文件夹名字     ==新建文件夹\033[0m       |\n" \
                    "| 5. \033[1;32m 指令: del 文件名/文件夹名   ==删除文件或文件夹\033[0m  |\n" \
                    "| 6. \033[1;32m 指令: get 文件名          ==从服务端下载文件  \033[0m |\n" \
                    "| 7. \033[1;32m 指令: put 文件名          ==客户端上传文件   \033[0m |\n" \
                    "| 8. \033[1;32m 指令: help               ==服务端帮助说明\033[0m    |\n" \
                    "🍕🍙🍜🍤😋🤗👦👸‍♂️🧝‍♀️🧝‍♀🎃🖼👵🥼‍🍳👨‍👨🧑👧👦🧒👶👨🧓"
        self.__send_head({
            "status": True,
            "help_text": help_text
        })

    def __server_run(self, head_dic):
        """
        根据客户端传递的指令,运行对应功能
        :param head_dic: 用户输入内容字典
        :return: None
        """
        if hasattr(self, "server_" + head_dic["cmd"]):         # 反射运行对应功能
            func = getattr(self, "server_" + head_dic["cmd"])
            if re.match(r"ls$|help$", head_dic["cmd"]):        # 如果是ls、help这些功能无参数运行
                func()
            else:
                func(head_dic)                                 # 启用对应功能
        else:
            self.__send_head({                                 # 无指定功能发送对应状态码
                "status": False,
                "status_code": STATUS_CODE["301"]
            })

    def __send_head(self, head_dic):
        """
        发送表头给客户端
        :param head_dic: 要发送的数据内容(字典形式)
        :return: None
        """
        head_bytes = json.dumps(head_dic).encode(self.coding)
        head_struct = struct.pack("i", len(head_bytes))
        self.conn.send(head_struct)
        self.conn.send(head_bytes)

    def __recv_head(self):
        """
        从客户端接受表头
        :return: 表头内容
        """
        head_struct = self.conn.recv(4)
        if not head_struct:
            return False
        head_size = struct.unpack("i", head_struct)[0]
        head_json = self.conn.recv(head_size).decode(self.coding)
        head_dic = json.loads(head_json)
        return head_dic

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
            mode = "上传"
        elif re.match("p$|put$", mode):
            mode = "下载"
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


if __name__ == '__main__':
    print("\033[1;31m请在statr.py文件运行本程序\033[0m")
