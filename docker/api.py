# -*- coding: utf-8 -*-
# api.py

from quart import Quart, request, jsonify, send_file
import hashlib, asyncio
import login as backend
import ddddocr
import json
import os
import requests
import re
import urllib.parse

run_host = "0.0.0.0"
run_port = 12345

ocr = ddddocr.DdddOcr(show_ad=False, beta=True)
ocrDet = ddddocr.DdddOcr(show_ad=False, beta=True, det=True)

class Account:
    def __init__(self, data):
        try:
            self.status = "pending"
            self.account = data.get("id")
            self.type = data.get("type", "password")
            self.remarks = data.get("remarks")
            self.password = data.get("pw")
            self.isAuto = data.get("isAuto", False)
            self.uid = hashlib.sha256((str(self.account) + str(self.password)).encode("utf-8")).hexdigest()

            if not self.account:
                raise ValueError("账号不能为空")
            if self.type == "password" and not self.password:
                raise ValueError("密码不能为空")
        except Exception as e:
            raise ValueError(f"账号密码错误: {str(e)}")

workList = {}

app = Quart(__name__)

def mr(status, **kwargs):
    r_data = {"status": status, **kwargs}
    response = jsonify(r_data)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

@app.route("/", methods=["GET"])
async def index():
    response = await send_file("index.html")
    response.headers.update({
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    })
    return response

@app.route("/login", methods=["POST"])
@app.route("/loginNew", methods=["POST"])
async def login():
    data = await request.get_json()
    return loginPublic(data)

async def THREAD_DO_LOGIN(uid):
    try:
        await backend.main(workList, uid, ocr, ocrDet)
    except Exception as e:
        print(e)
        workList[uid].msg = str(e)

@app.route("/check", methods=["POST"])
async def check():
    data = await request.get_json()
    uid = data.get("uid")

    if uid in workList:
        account = workList[uid]
        status = account.status

        if status == "pass":
            ql_api = QLAPI()
            ql_api.load_config()
            ql_api.get_token()

            if ql_api.get_ck():
                ql_api.check_ck(account.cookie, account.remarks)

            ptpin = extract_pt_pin(account.cookie)
            account_data = {
                "account": account.account,
                "password": account.password,
                "ptpin": ptpin,
                "remarks": account.remarks,
                "wxpusherUid": ""
            }

            if not account_exists(account_data):
                save_account_data(account_data)
                if ql_api.isWxPusher:
                    loginNotify(ql_api.wxpusherAppToken, ql_api.wxpusherAdminUid, f"账号 {ptpin} 登录成功")

            return mr(status, cookie=account.cookie, msg="成功")
        
        if status in ["pending", "error", "SMS", "wrongSMS"]:
            return mr(status, msg=get_status_message(status, account.msg))
        return mr("error", msg=f"笨蛋开发者，忘记适配新状态啦：{status}")

    return mr("error", msg="未找到该账号记录，请重新登录")

@app.route("/sms", methods=["POST"])
async def sms():
    data = await request.get_json()
    uid = data.get("uid")
    code = data.get("code")

    if not validate_sms_code(code):
        return mr("wrongSMS", msg="验证码错误")

    try:
        THREAD_SMS(uid, code)
        return mr("pass", msg="成功提交验证码")
    except Exception as e:
        return mr("error", msg=str(e))

def loginNotify(token, uid, content):
    encoded_content = urllib.parse.quote(content)
    url = f"https://wxpusher.zjiecode.com/api/send/message/?appToken={token}&content={encoded_content}&uid={uid}&url=http%3a%2f%2fbaidu.com"
    requests.get(url)

def loginPublic(data):
    try:
        u = Account(data)
    except Exception as e:
        return mr("error", msg=str(e))

    if u.uid in workList:
        workList[u.uid].SMS_CODE = None
        return mr("pass", uid=u.uid, msg=f"{u.account}已经在处理了，请稍后再试")

    workList[u.uid] = u
    asyncio.create_task(THREAD_DO_LOGIN(u.uid))
    return mr("pass", uid=u.uid, msg=f"{u.account}处理中, 到/check查询处理进度")

def THREAD_SMS(uid, code):
    account = workList.get(uid)
    if not account:
        raise ValueError("账号不在记录中")

    if account.status in ["SMS", "wrongSMS"]:
        account.SMS_CODE = code
    else:
        raise ValueError("账号不在SMS过程中")

@app.route("/get", methods=["GET"])
async def get_data():
    config = load_from_file("config.json")
    param_k = request.args.get("k")

    if param_k == config.get("key"):
        data = load_from_file("data.json")
        return jsonify(data)
    return jsonify([])

@app.route("/status", methods=["GET"])
async def checkql():
    ql_api = QLAPI()
    try:
        ql_api.load_config()
        ql_api.get_token()

        if ql_api.qltoken is None:
            return mr("wrongQL", msg="存储容器检测失败, 请检查参数是否正确", data={"name": ql_api.name, "notice": ql_api.notice, "isPush": ql_api.isWxPusher})

        return mr("pass", msg="存储容器检测成功", data={"name": ql_api.name, "notice": ql_api.notice, "isPush": ql_api.isWxPusher})

    except:
        return mr("wrongFile", msg="存储容器检测失败, 请检查config.json", data={})

def extract_pt_pin(cookie_string):
    match = re.search(r"pt_pin=([^;]+)", cookie_string)
    return match.group(1) if match else ""

@app.route("/qrcode", methods=["POST"])
async def createQrCode():
    data = await request.get_json()
    result = createQrCodeApi(data.get('params', ''))

    if result:
        return mr("pass", msg='ok', data=result)
    return mr("error", msg='error', data='')

def createQrCodeApi(params):
    ql_api = QLAPI()
    ql_api.load_config()

    url = "https://wxpusher.zjiecode.com/api/fun/create/qrcode"
    payload = {"appToken": ql_api.wxpusherAppToken, "extra": params, "validTime": 300}
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        if result.get("code") == 1000:
            return result.get("data", {}).get("url")
        print(f"API Error: {result.get('msg', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return False

@app.route("/wxpushercallback", methods=["POST"])
async def wxpushercallback():
    params = await request.get_json()
    uid = params.get('data', {}).get('uid', '')
    extra = params.get('data', {}).get('extra', '')

    data = load_from_file("data.json")
    for item in data:
        if item["ptpin"] == extra:
            item["wxpusherUid"] = uid
            save_to_file("data.json", data)
            return mr("pass", msg='ok', data=item)

    return mr("error", msg='Item not found', data='')

# Utility functions
def load_from_file(filename):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_to_file(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存到文件时出错: {e}")

def account_exists(account_data):
    existing_data = load_from_file("data.json")
    return any(
        item["account"] == account_data["account"] and item["password"] == account_data["password"]
        for item in existing_data
    )

def save_account_data(account_data):
    existing_data = load_from_file("data.json")
    existing_data.append(account_data)
    save_to_file("data.json", existing_data)

def get_status_message(status, message):
    status_messages = {
        "pending": "登录处理中，请稍等",
        "error": f"登录出错：{message}",
        "SMS": "验证码已发送，请检查短信",
        "wrongSMS": "验证码错误，请重新输入",
    }
    return status_messages.get(status, f"未处理的状态: {status}")

def validate_sms_code(code):
    return code and len(code) == 6


class QLAPI:
    def __init__(self):
        self.config_file = "config.json"
        self.ql_isNewVersion = True
        self.qltoken = None
        self.qlhd = None
        self.qlhost = None
        self.qlid = None
        self.qlsecret = None
        self.qlenvs = []
        self.name = "GoDongGoCar"
        self.notice = "欢迎光临"
        self.wxpusherAppToken = None
        self.wxpusherAdminUid = None
        self.isWxPusher = False

    def load_config(self):
        # print(os.getcwd())
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 组合脚本目录与文件名形成相对路径
        file_path = os.path.join(script_dir, self.config_file)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        self.qlhost = config["ql_host"]
        self.qlid = config["ql_app_id"]
        self.qlsecret = config["ql_app_secret"]
        self.ql_isNewVersion = config["ql_isNewVersion"]
        self.name = config["name"]
        self.notice = config["notice"]
        self.wxpusherAppToken = config["wxpusherAppToken"]
        self.wxpusherAdminUid = config["wxpusherAdminUid"]
        self.isWxPusher = config["isWxPusher"]

    def get_token(self):
        # print(self.qlhost)
        url = f"{self.qlhost}/open/auth/token?client_id={self.qlid}&client_secret={self.qlsecret}"
        print(url)
        response = requests.get(url)
        res = response.json()
        if res.get("code") == 200:
            self.qltoken = res["data"]["token"]
            self.qlhd = {
                "Authorization": f"Bearer {self.qltoken}",
                "accept": "application/json",
                "Content-Type": "application/json",
            }

    def get_ck(self):
        url = f"{self.qlhost}/open/envs?searchValue=JD_COOKIE&t={int(time.time())}"
        response = requests.get(url, headers=self.qlhd)
        res = response.json()
        if res.get("code") == 200:
            self.qlenvs = res["data"]
            return True
        else:
            return False

    def update_env(self, name, value, id, remarks):
        if self.ql_isNewVersion:
            params = {"name": name, "value": value, "id": id, "remarks": remarks}
        else:
            params = {"name": name, "value": value, "_id": id, "remarks": remarks}
        url = f"{self.qlhost}/open/envs"
        response = requests.put(url, headers=self.qlhd, data=json.dumps(params))
        res = response.json()
        if res.get("code") == 200:
            return True
        else:
            return False

    def create_env(self, name, value, remarks):
        params = [{"value": value, "name": name, "remarks": remarks}]
        url = f"{self.qlhost}/open/envs"
        response = requests.post(url, headers=self.qlhd, data=json.dumps(params))
        res = response.json()
        if res.get("code") == 200:
            return True
        else:
            return False

    def check_ck(self, ck, remarks):
        # 这里获取到CK的状态 1 失效
        # 正则取出pt_pin=后面的值
        # print(self.qlenvs)
        # FOR循环 找到extract_pt_pin(value) 和 extract_pt_pin(cookie) 相同的 如果不同则继续循环 如果循环结束 还是没有 则调用creat_env
        for i in self.qlenvs:
            if extract_pt_pin(i["value"]) == extract_pt_pin(ck):
                if self.ql_isNewVersion:
                    self.update_env(i["name"], ck, i["id"], remarks)
                else:
                    self.update_env(i["name"], ck, i["_id"], remarks)
                if i["status"] == 1:
                    if self.ql_isNewVersion:
                        self.enable_ck(i["id"])
                    else:
                        self.enable_ck(i["_id"])
                return
        self.create_env("JD_COOKIE", ck, remarks)

    def enable_ck(self, id):
        params = [id]
        url = f"{self.qlhost}/open/envs/enable"
        response = requests.put(url, headers=self.qlhd, data=json.dumps(params))
        res = response.json()
        if res.get("code") == 200:
            return True
        else:
            return False


# 创建本线程的事件循环，运行flask作为第一个任务
# asyncio.new_event_loop().run_until_complete(app.run(host=run_host, port=run_port))
# 确保 app.run 是一个协程函数
"""
async def start_app():
    await app.run(host=run_host, port=run_port)

# 然后将协程传递给 run_until_complete
loop = asyncio.get_event_loop()
if loop.is_running():
        # If a loop is already running, use it to run the app
    asyncio.ensure_future(start_app())
else:
    loop.run_until_complete(start_app())
"""

# asyncio.new_event_loop().run_until_complete(start_app())
