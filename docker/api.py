from quart import Quart, request, jsonify, send_from_directory, send_file
import hashlib, asyncio
import login as backend
import ddddocr
import json
import os
import requests
import re
import time
# 初始化 OCR
def init_ocr():
    return ddddocr.DdddOcr(show_ad=False, beta=True), ddddocr.DdddOcr(show_ad=False, beta=True, det=True)

ocr, ocrDet = init_ocr()

class Account:
    def __init__(self, data):
        self.status = "pending"
        self.account = data.get("id")
        self.type = data.get("type", "password")
        self.remarks = data.get("remarks")
        self.password = data.get("pw")
        self.isAuto = data.get("isAuto", False)
        self.uid = self.generate_uid()
        
        if not self.account:
            raise ValueError("账号不能为空")
        if self.type == "password" and not self.password:
            raise ValueError("密码不能为空")
    
    def generate_uid(self):
        c = f"{self.account}{self.password}"
        return hashlib.sha256(c.encode("utf-8")).hexdigest()

# 正在处理的账号列表
workList = {}

app = Quart(__name__)

def mr(status, **kwargs):
    r_data = {"status": status}
    r_data.update(kwargs)
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
async def login():
    data = await request.get_json()
    return loginPublic(data)

@app.route("/loginNew", methods=["POST"])
async def loginNew():
    data = await request.get_json()
    return loginPublic(data)

async def THREAD_DO_LOGIN(workList, uid, ocr, ocrDet):
    try:
        await backend.main(workList, uid, ocr, ocrDet)
    except Exception as e:
        workList[uid].msg = str(e)

@app.route("/check", methods=["POST"])
async def check():
    data = await request.get_json()
    uid = data.get("uid")

    if uid in workList:
        account_info = workList[uid]
        status_message = get_status_message(account_info.status, account_info.msg)
        
        if account_info.status == "pass":
            handle_login_success(account_info)

        return mr(account_info.status, msg=status_message, cookie=account_info.cookie if account_info.status == "pass" else None)

    return mr("error", msg="未找到该账号记录，请重新登录")

def handle_login_success(account_info):
    ql_api = QLAPI()
    ql_api.load_config()
    ql_api.get_token()

    if ql_api.get_ck():
        ql_api.check_ck(account_info.cookie, account_info.remarks)
    
    ptpin = extract_pt_pin(account_info.cookie)
    account_data = {
        "account": account_info.account,
        "password": account_info.password,
        "ptpin": ptpin,
        "remarks": account_info.remarks,
        "wxpusherUid": ""
    }
    
    update_json_data("data.json", account_data)

    if ql_api.isWxPusher:
        loginNotify(ql_api.wxpusherAppToken, ql_api.wxpusherAdminUid, f"账号 {ptpin} 登录成功")

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
    asyncio.create_task(THREAD_DO_LOGIN(workList, u.uid, ocr, ocrDet))
    return mr("pass", uid=u.uid, msg=f"{u.account}处理中, 到/check查询处理进度")

def THREAD_SMS(uid, code):
    account_info = workList.get(uid)
    
    if account_info and account_info.status in ["SMS", "wrongSMS"]:
        account_info.SMS_CODE = code
    else:
        raise ValueError("账号不在SMS过程中")

def extract_pt_pin(cookie_string):
    match = re.search(r"pt_pin=([^;]+)", cookie_string)
    return match.group(1) if match else ""

def load_from_file(filename):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_to_file(filename, data):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_json_data(filename, account_data):
    existing_data = load_from_file(filename)
    if not any(item["account"] == account_data["account"] and item["password"] == account_data["password"] for item in existing_data):
        existing_data.append(account_data)
        save_to_file(filename, existing_data)

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