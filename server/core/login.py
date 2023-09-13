# -*- coding:utf-8 -*-

import os
import hashlib
from conf import settings
from core import db_handler

# 获取取MD5编码
CODING = settings.MD5_CODING
# 获取状态码
STATUS_CODE = settings.STATUS_CODE
# 获取用户状态
user_status = db_handler.user_status
#
SERVER_DIR = settings.SERVER_DIR


def account_auth(username, pwd):
    if user_status["status"] and user_status["username"] == username:
        return settings.STATUS_CODE["206"], 0
    md5 = hashlib.md5()
    md5.update(pwd.encode(CODING))
    pwd = md5.hexdigest()
    account_login = db_handler.Account.account_load("login")
    for i in account_login:
        if i["username"] == username:
            user_home_path = os.path.join(SERVER_DIR["account_home_path"], username)
            if i["status"] is True:
                if i["pwd"] == pwd:
                    user_status["username"] = username
                    user_status["status"] = True
                    db_handler.user_status["current_dir"] = user_home_path
                    db_handler.user_status["home_dir"] = user_home_path
                    return STATUS_CODE["200"], True
                else:
                    return STATUS_CODE["202"], True
            elif i["status"] <= settings.MAX_LOGIN_COUNT:
                if i["pwd"] == pwd:
                    user_status["username"] = username
                    user_status["status"] = True
                    db_handler.Account.account_modify(username, "status", 0)
                    db_handler.user_status["current_dir"] = user_home_path
                    db_handler.user_status["home_dir"] = user_home_path
                    return STATUS_CODE["200"], 0
                else:
                    db_handler.Account.account_modify(username, "status", i["status"]+1)
                    print(i["status"])
                    return STATUS_CODE["202"], i["status"]+1
            else:
                return STATUS_CODE["204"], i["status"]
    else:
        return STATUS_CODE["203"], False


def account_out(username, pwd):
    if user_status["username"] == username:
        account_list = db_handler.Account.account_load("account")
        md5 = hashlib.md5()
        md5.update(pwd.encode(CODING))
        pwd = md5.hexdigest()
        for i in account_list:
            if i["username"] == username:
                if i["pwd"] == pwd:
                    user_status["status"] = False
                    user_status["username"] = None
                    return [STATUS_CODE["300"], STATUS_CODE["207"]]
                else:
                    return [STATUS_CODE["300"], STATUS_CODE["202"]]
        else:
            return [STATUS_CODE["300"], STATUS_CODE["203"]]
    else:
        return [STATUS_CODE["300"], STATUS_CODE["205"]]
