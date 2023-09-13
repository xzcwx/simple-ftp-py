# -*- coding:utf-8 -*-
"""
此文件(db_handler.py)为控制所有文件读取功能
返回的内容均为状态码内容,不能为状态码(数字)
"""

import os
import re
import json
import shutil
import shelve
import hashlib

from conf import settings

# 获取状态码
STATUS_CODE = settings.STATUS_CODE
# 获取服务端目录
SERVER_DIR = settings.SERVER_DIR
# 获取客户端文件目录
FILE_DIR = settings.FILE_DIR
# 获取取MD5编码
CODING = settings.MD5_CODING

# 定义用户状态
user_status = {
    "username": None,
    "status": False,
    "home_dir": None,
    "current_dir": ""
}


class Account(object):
    """用户配置文件管理类"""
    FILE_PATH = FILE_DIR["account_file"]                                   # 获取配置文件目录
    newfile_name = f"~${os.path.basename(FILE_PATH)[1:]}"                  # 定义临时文件名
    newfile_path = os.path.join(os.path.dirname(FILE_PATH), newfile_name)  # 定义临时文件目录

    @classmethod
    def account_load(cls, obj):
        """
        用户配置文件读取功能
        :param obj: 读取内容选择
        :return: 返回obj所指定读取内容
        """
        if isinstance(obj, str):
            with open(cls.FILE_PATH, "r") as f_r:
                data_list = json.load(f_r)
            if re.match(r"account$", obj):                       # 返回所有参数
                return data_list
            elif re.match(r"name$", obj):
                name_list = [i["username"] for i in data_list]   # 返回用户名参数
                return name_list
            elif re.match(r"login$", obj):
                login_list = [{
                    "username": i["username"],
                    "pwd": i["pwd"],
                    "status": i["status"]
                } for i in data_list]
                return login_list                                # 返回用户名、密码、状态参数
            elif re.match(r"status$", obj):
                status_list = [{
                    "username": i["username"],
                    "status": i["status"],
                    "size": i["size"]
                } for i in data_list]
                return status_list                               # 返回用户名、状态、Home目录大小
            else:
                return STATUS_CODE["100"]
        else:
            return STATUS_CODE["101"]

    @classmethod
    def account_save(cls, account_dic, genre="user"):
        """
        用户配置文件存储功能
        :param account_dic: 需要存储的新用户数据,字典格式,有username、pwd 参数
        :param genre: 用户类型，默认为 user(普通用户)
        :return: 状态码或其内容
        """
        md5 = hashlib.md5()
        if isinstance(account_dic, dict):
            if len(account_dic) == 2:
                if re.match(r"user$", genre):
                    account_dic["status"] = 0                           # 普通用户启用状态记录次数,初始0
                    account_dic["size"] = 1 * 1024**3                   # 普通用户默认1GB存储空间
                elif re.match(r"admin$", genre):
                    account_dic["status"] = True                        # 管理员用户为True,为无限次
                    account_dic["size"] = True                          # 管理员用户为True,为无限次
                with open(cls.newfile_path, "w") as f_n:
                    with open(cls.FILE_PATH, "r") as f_r:
                        data_list = json.load(f_r)
                        for i in data_list:                             # 判断是否有重复的用户名
                            if i["username"] == account_dic["username"]:
                                return STATUS_CODE["211"]
                        md5.update(account_dic["pwd"].encode(CODING))
                        account_dic["pwd"] = md5.hexdigest()
                        data_list.append(account_dic)
                        json.dump(data_list, f_n)
                os.replace(cls.newfile_path, cls.FILE_PATH)
                ret_status = File.mkdir_home(account_dic["username"])   # 生成用户的Home目录
                return STATUS_CODE["208"], ret_status
            else:
                return STATUS_CODE["106"]
        else:
            return STATUS_CODE["101"]

    @classmethod
    def account_modify(cls, account, obj, data):
        """
        用户配置文件内容修改功能
        :param account: 所需要修改的用户名
        :param obj: 要修改参数对象
        :param data: 修改后的内容
        :return: 状态码或其内容
        """
        # 判断需要修改的参数对象传入是否合规存在
        if isinstance(obj, str):
            if re.match(r"pwd$", obj):
                # 若是修改密码,将密码MD5值加密
                md5 = hashlib.md5()
                md5.update(data.encode(CODING))
                data = md5.hexdigest()
            elif re.match(r"username$", obj):
                pass
            elif re.match(r"status$", obj):
                pass
            elif re.match(r"size$", obj):
                pass
            else:
                return STATUS_CODE["100"]
        else:
            return STATUS_CODE["101"]

        status = False                                # 参数修改是否成功状态
        new_data_list = []
        with open(cls.newfile_path, "w") as f_n:
            with open(cls.FILE_PATH, "r") as f_r:
                data_list = json.load(f_r)
                for i in data_list:
                    if i["username"] == account:
                        i[obj] = data
                        new_data_list.append(i)
                        status = True
                    else:
                        new_data_list.append(i)
            json.dump(new_data_list, f_n)
        os.replace(cls.newfile_path, cls.FILE_PATH)  # 将临时文件替换成源文件
        if status:
            return STATUS_CODE["201"]
        else:
            return STATUS_CODE["203"]

    @classmethod
    def account_del(cls, username):
        """
        配置文件删除指定用户功能
        :param username: 所删除的用户名
        :return: 状态码或其内容
        """
        status = False                               # 删除是否成功状态
        with open(cls.newfile_path, "w") as f_n:
            with open(cls.FILE_PATH, "r") as f_r:
                data_list = json.load(f_r)
                for i in data_list:
                    if i["username"] == username:
                        data_list.remove(i)          # 删除指定用户
                        status = True
                json.dump(data_list, f_n)
        os.replace(cls.newfile_path, cls.FILE_PATH)  # 将临时文件替换成源文件
        if status:
            return STATUS_CODE["209"]
        else:
            return STATUS_CODE["203"]


class File(object):  
    """数据文件处理类"""
    HOME_DIR = SERVER_DIR["account_home_path"]

    @classmethod
    def home_mkdir(cls, username):
        """
        账户Home目录生成功能
        :param username: 用户名
        :return: 状态码或其内容
        """
        if isinstance(username, str):
            account_list = Account.account_load("name")             # 读取用户配置文件,返回name对象
            for i in account_list:
                if i == username:                                   # 判断用户名是否存在
                    if not os.path.isdir(os.path.join(cls.HOME_DIR, username)):
                        os.mkdir(os.path.join(cls.HOME_DIR, username))
                        return STATUS_CODE["400"]
                    else:
                        return STATUS_CODE["401"]
            else:                                                   # 循环结束用户名不存在返回状态码
                return STATUS_CODE["203"]
        else:
            return STATUS_CODE["101"]

    @classmethod
    def home_size(cls, username, size="1GB"):
        """
        配置Home目录大小功能
        :param username: 用户名
        :param size: 指定Home目录可存储大小，现支持GB、MB、KB、B单位容量
        :return: 状态码或其内容
        """
        # 将容量单位统一转化为 B 字节单位
        if re.match(r"\d+\s?B$", size, flags=re.I):             # 匹配 B 容量单位
            size = re.match(r"(\d+)\s?B$", size, flags=re.I).groups()[0]
            pass
        elif re.match(r"\d+\s?KB$", size, flags=re.I):          # 匹配 KB 容量单位
            size = re.match(r"(\d+)\s?KB$", size, flags=re.I).groups()[0]
            size = int(size) * 1024
        elif re.match(r"\d+\s?MB$", size, flags=re.I):          # 匹配 MB 容量单位
            size = re.match(r"(\d+)\s?MB$", size, flags=re.I).groups()[0]
            size = int(size) * 1024**2
        elif re.match(r"\d+\s?GB$", size, flags=re.I):          # 匹配 GB 容量单位
            size = re.match(r"(\d+)\s?GB$", size, flags=re.I).groups()[0]
            size = int(size) * 1024**3
        elif re.match(r"\d+\s?TB$", size, flags=re.I):          # 匹配 TB 容量单位
            size = re.match(r"(\d+)\s?TB$", size, flags=re.I).groups()[0]
            size = int(size) * 1024**4
        else:
            return STATUS_CODE["100"]
        account_list = Account.account_load("status")
        for i in account_list:
            if i["username"] == username:                       # 寻找对应的用户
                if i["size"] is True:                           # 如果为True状态(管理员)
                    return STATUS_CODE["210"]
                break
        ret_status = Account.account_modify(username, "size", size)   # 调用参数修改功能
        return ret_status                                       # 返回状态内容

    @classmethod
    def mkdir_home(cls, username, mode="new"):
        """
        Home目录文件夹新建和判断功能
        :param username: 用户名
        :param mode: 选择模式，默认new是新建模式，judg为判断模式
        :return: 状态码或其内容
        """
        user_path = os.path.join(cls.HOME_DIR, username)
        if os.path.isdir(user_path):
            return STATUS_CODE["401"]
        else:
            os.mkdir(user_path)
            if re.match(r"new$", mode):     # 判断是否新建模式
                return STATUS_CODE["400"]
            elif re.match(r"judg$", mode):  # 判断是否Home目录存在模式
                return [STATUS_CODE["402"], STATUS_CODE["403"]]

    @staticmethod
    def mkdir_dir(dir_name):
        dir_path = os.path.join(user_status["current_dir"], dir_name)
        if os.path.isdir(dir_path):
            return [STATUS_CODE["300"], STATUS_CODE["410"]]
        else:
            os.mkdir(dir_path)
            return [STATUS_CODE["300"], STATUS_CODE["404"]]

    @classmethod    
    def del_home(cls, username):
        """
        删除Home目录功能
        :param username: 用户名
        :return: 状态码或其内容
        """
        user_path = os.path.join(cls.HOME_DIR, username)
        if os.path.isdir(user_path):
            shutil.rmtree(os.path.join(user_path))        # 用shutil 递归树删除文件夹
            return STATUS_CODE["405"]
        else:
            return STATUS_CODE["410"]

    @classmethod
    def del_dir(cls, target_dir):
        """
        目录删除功能
        :param target_dir: 需要删除的目标名
        :return: 状态码或其内容,目标名不存在返回False
        """
        ls_dic = cls.ls_data()
        del_dir = os.path.join(user_status["current_dir"], target_dir)
        if target_dir in ls_dic["文件"]:                      # 判断是否为文件
            os.remove(del_dir)
            return [STATUS_CODE["300"], STATUS_CODE["409"]]
        elif target_dir in ls_dic["文件夹"]:                  # 判断是否为文件夹
            shutil.rmtree(del_dir)
            return [STATUS_CODE["300"], STATUS_CODE["405"]]
        else:
            return False                                     # 目标名不存在返回False

    @staticmethod
    def ls_data(mode="a"):
        """
        获取当前目录所有文件内容及文件夹内容功能
        :param mode: a 模式为文件名列表和文件夹名列表字典,
                     f 模式为文件名列表, d 模式为文件夹名列表
        :return: 根据模式返回指定内容
        """
        dir_path = user_status["current_dir"]
        if os.path.isdir(dir_path):
            ls_dic = {"文件": [], "文件夹": []}
            dir_list = os.listdir(user_status["current_dir"])
            for i in dir_list:
                if re.match(r".+\.\w+", i):                  # 匹配文件名
                    ls_dic["文件"].append(i)
                else:
                    ls_dic["文件夹"].append(i)
            if re.match("a$|all$", mode):
                return ls_dic
            elif re.match("f$|file$", mode):
                return ls_dic["文件"]
            elif re.match("d$|dir$", mode):
                return ls_dic["文件夹"]
            else:
                raise ValueError("传入模式参数值错误")
        else:
            return False

    @staticmethod
    def md5_load(file_path):
        """
        MD5加密功能
        :param file_path: 需要MD5加密文件的目录
        :return: MD5 16进制 加密结果
        """
        md5 = hashlib.md5()
        file_size = os.path.getsize(file_path)
        md5_data, read_size = b"", 0
        with open(file_path, "rb") as f:
            while read_size < file_size:
                file_data = f.read(file_size // 4)
                if read_size == 0:  # 开头
                    md5_data += file_data[:10]
                elif read_size >= file_size // 4 * 3:
                    md5_data += file_data[:10]
                elif read_size >= file_size // 4 * 2:
                    md5_data += file_data[:10]
                read_size += len(file_data)
            else:
                md5_data += file_data[-10:]  # 结尾
        md5.update(md5_data)
        return md5.hexdigest()

    @classmethod
    def dirsize_judg(cls, username, file_size):
        """
        用户目录大小判断功能
        :param username: 用户名
        :param file_size: 新增文件大小
        :return: 空间足够或者为管理员返回True,空间不足返回False
        """
        account_status = Account.account_load("status")
        user_size = None
        for i in account_status:
            if i["username"] == username:
                user_size = i["size"]
                break
        if user_size is True:
            return True
        current_size = cls.get_dirsize(username)
        if current_size is not False:
            if (current_size + file_size) > user_size:
                return False
            else:
                return True
               
    @staticmethod
    def get_dirsize(username):
        """
        用户目录大小查询功能
        :param username: 用户名
        :return: 用户目录存在放回其大小,不存在返回False
        """
        user_home_dir = os.path.join(SERVER_DIR["account_home_path"], username)
        if os.path.isdir(user_home_dir):
            home_size = os.path.getsize(user_home_dir)
            print(f"\033[1;32m{home_size}\033[0m")
            return home_size
        else:
            return False

    @staticmethod
    def get_path(file_name):
        current_dir = user_status["current_dir"]
        rule = re.match(f".+home(.*)", current_dir)
        if rule:
            return os.path.join(rule.groups()[0], file_name)

    @staticmethod
    def temp_file(mode, file_info=None, temp_name=None):
        """
        文件下载信息保存、读取 功能
        :param mode: 操作模式
        :param file_info: 文件信息字典
        :param temp_name: 临时文件名
        :return: 状态码或其内容
        """
        temp_file_path = os.path.join(SERVER_DIR["temp_path"], settings.TEMP_INFO)
        if file_info is not None:
            if re.match(r"write$|w$", mode, flags=re.I):
                with shelve.open(temp_file_path) as f_t:
                    f_t[file_info["file_name"]] = {
                        "file_name": file_info["file_name"],
                        "file_size": file_info["file_size"],
                        "file_md5": file_info["file_md5"],
                        "file_path": file_info["file_path"]
                    }
                    return {
                        "status": True,
                        "status_code": STATUS_CODE["502"]
                    }
            else:
                return {
                    "status": False,
                    "status_code": STATUS_CODE["103"]
                }
        elif temp_name is not None:
            rule = re.match(rf"(.+)\.{settings.TEMP_NAME}", temp_name)
            if rule:
                file_name = rule.groups()[0]
                if re.match(r"read$|r$", mode, flags=re.I):
                    with shelve.open(temp_file_path) as f_t:
                        if file_name in f_t:
                            file_info = f_t[file_name]
                            return {
                                "status": True,
                                "status_code": STATUS_CODE["503"],
                                "file_info": file_info
                            }
                        else:
                            return {
                                "status": False,
                                "status_code": STATUS_CODE["505"]
                            }
                elif re.match(r"del$|d$", mode, flags=re.I):
                    if temp_name is not None:
                        with shelve.open(temp_file_path) as f_t:
                            if file_name in f_t:
                                del f_t[file_name]
                                return {
                                    "status": True,
                                    "status_code": STATUS_CODE["504"]
                                }
                            else:
                                return {
                                    "status": False,
                                    "status_code": STATUS_CODE["505"]
                                }
                else:
                    return {
                        "status": False,
                        "status_code": STATUS_CODE["103"]
                    }
        else:
            raise ValueError("传入参数缺失")
