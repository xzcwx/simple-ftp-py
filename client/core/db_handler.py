# -*- coding:utf-8 -*-

import os
import re
import shelve
import hashlib

from conf import settings


# 获取客户端目录
CLIENT_DIR = settings.CLIENT_DIR
# 获取客户端文件目录
FILE_DIR = settings.FILE_DIR


class File(object):
    
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

    @staticmethod
    def ls_data(mode="a"):
        """
        获取当前目录所有文件内容及文件夹内容功能
        :param mode: a 模式为文件名列表和文件夹名列表字典,
                     f 模式为文件名列表, d 模式为文件夹名列表
        :return: 根据模式返回指定内容
        """
        if os.path.isdir(CLIENT_DIR["file_path"]):
            ls_dic = {"文件": [], "文件夹": []}
            dir_list = os.listdir(CLIENT_DIR["file_path"])
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
    def temp_file(mode, file_info=None, temp_name=None):
        """
        文件下载信息保存、读取 功能
        :param mode: 操作模式
        :param file_info: 文件信息字典
        :param temp_name: 临时文件名
        :return: 状态码或其内容
        """
        temp_file_path = os.path.join(CLIENT_DIR["temp_path"], settings.TEMP_INFO)
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
                        "status_code": settings.STATUS_CODE["502"]
                    }
            else:
                return {
                    "status": False,
                    "status_code": settings.STATUS_CODE["103"]
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
                                "status_code": settings.STATUS_CODE["503"],
                                "file_info": file_info
                            }
                        else:
                            return {
                                "status": False,
                                "status_code": settings.STATUS_CODE["505"]
                            }
                elif re.match(r"del$|d$", mode, flags=re.I):
                    if temp_name is not None:
                        with shelve.open(temp_file_path) as f_t:
                            if file_name in f_t:
                                del f_t[file_name]
                                return {
                                    "status": True,
                                    "status_code": settings.STATUS_CODE["504"]
                                }
                            else:
                                return {
                                    "status": False,
                                    "status_code": settings.STATUS_CODE["505"]
                                }
                else:
                    return {
                        "status": False,
                        "status_code": settings.STATUS_CODE["103"]
                    }
        else:
            raise ValueError("传入参数缺失")

