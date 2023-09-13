# -*- coding:utf-8 -*-

import os


"""
+--------------------------------------------------------------------+
|                             服务端路径配置                            |
+--------------------------------------------------------------------+
"""

# 服务端根目录
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# 服务端目录
SERVER_DIR = {
    "log_path": os.path.join(BASE_DIR, "logs"),
    "account_db_path": os.path.join(BASE_DIR, "db"),
    "account_home_path": os.path.join(BASE_DIR, "home"),
    "temp_path": os.path.join(BASE_DIR, "home/temp")
}

# 服务端文件目录
FILE_DIR = {
    "log_file": os.path.join(SERVER_DIR["log_path"], "server.log"),
    "account_file": os.path.join(SERVER_DIR["account_db_path"], "user_info.ini"),
    # "home_file": os.path.join(SERVER_DIR["account_db_path"], "user_home_info.ini")
}

# 文件下载信息保存文件名(无后缀)
TEMP_INFO = "temp"

# 临时下载文件后缀名
TEMP_NAME = "xzdownload"

"""
+--------------------------------------------------------------------+
|                          服务端返回状态码配置                          |
+--------------------------------------------------------------------+
"""

# 服务端状态码大全(谨慎更改)
STATUS_CODE = {
    "100": [100, "传入参数格式错误"],
    "101": [101, "传入参数数据类型错误"],
    "102": [102, "传入参数为空"],
    "103": [103, "输入参数识别失败"],
    "104": [104, "超级密码认证失败"],
    "105": [105, "返回成功"],
    "106": [106, "输入参数元素量错误"],
    "107": [107, "输入参数范围错误"],
    "200": [200, "用户认证成功"],
    "201": [201, "用户参数修改成功"],
    "202": [202, "用户密码错误"],
    "203": [203, "该用户名不存在"],
    "204": [204, "该用户已被锁定"],
    "205": [205, "该用户未登录"],
    "206": [206, "该用户重复登录"],
    "207": [207, "用户退出登录成功"],
    "208": [208, "添加用户成功"],
    "209": [209, "删除用户成功"],
    "210": [210, "管理员账户没上限，不可更改"],
    "211": [211, "该用户名已存在"],
    "300": [300, "cmd 指令成功"],
    "301": [301, "cmd 指令不存在"],
    "302": [302, "cmd 指令错误"],
    "303": [303, "客户端传递用户名参数缺失"],
    "400": [400, "Home目录创建成功"],
    "401": [401, "Home目录已存在"],
    "402": [402, "用户Home目录不存在"],
    "403": [403, "用户Home重置成功"],
    "404": [404, "文件夹创建成功"],
    "405": [405, "文件夹删除成功"],
    "406": [406, "文件获取成功"],
    "407": [407, "文件上传成功"],
    "408": [408, "文件下载完成"],
    "409": [409, "文件删除成功"],
    "410": [410, "该目录已存在"],
    "411": [411, "用户目标文件不存在"],
    "412": [412, "用户目标目录不存在"],
    "413": [413, "用户目录获取成功"],
    "414": [414, "用户目录不存在"],
    "415": [415, "目标目录切换成功"],
    "416": [416, "上级目录切换成功"],
    "417": [417, "当前所在顶层目录"],
    "418": [418, "Home目录返回成功"],
    "419": [419, "该文件已存在"],
    "420": [420, "用户存储空间不足"],
    "421": [421, "文件夹名错误"],
    "500": [500, "文件MD5校验成功"],
    "501": [501, "文件MD5校验失败"],
    "502": [502, "文件数据保存成功"],
    "503": [503, "文件数据获取成功"],
    "504": [504, "文件数据删除成功"],
    "505": [505, "文件数据获取失败"],
}


"""
+--------------------------------------------------------------------+
|                             服务端参数配置                            |
+--------------------------------------------------------------------+
"""

# 传输默认编码类型
CS_CODING = "utf-8"
# 账户默认加密编码类型
MD5_CODING = "utf-8"

# 最大客户端链接监听数
REQUEST_QUEUE_SIZE = 5
# 最大传输收取大小
MAX_PACKET_SIZE = 8192
# 服务器IP
HOST = "127.0.0.1"
# 端口号
PORT = 9088

"""
+--------------------------------------------------------------------+
|                       用户登录认证参数相关配置                          |
+--------------------------------------------------------------------+
"""

# 最大登录失败次数
MAX_LOGIN_COUNT = 5
# 最大登录异常尝试次数
MAX_LOGIN_TRY = 3
# 超级管理密码
SUPER_PWD = "qwe123"