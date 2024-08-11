# -*- coding: utf-8 -*-
# api.py
run_host = "0.0.0.0"
run_port = 12345


from quart import Quart, request, jsonify, send_from_directory,send_file
import hashlib, asyncio
import login as backend
import ddddocr
import json
import os

ocr = ddddocr.DdddOcr(show_ad=False, beta=True)
ocrDet = ddddocr.DdddOcr(show_ad=False, beta=True, det=True)


class account:
    status = ""
    uid = ""
    account = ""
    password = ""
    isAuto = False
    type = ""
    cookie = ""
    SMS_CODE = ""
    msg = ""

    def __init__(self, data):
        try:
            self.status = "pending"
            self.account = data.get("id", None)
            self.type = data.get("type", None)
            self.password = data.get("pw", None)
            self.isAuto = data.get("isAuto", False)
            if not self.account:
                raise ValueError("账号不能为空")
                if type == "password" and not self.password:
                    raise ValueError("密码不能为空")

            c = str(self.account) + str(self.password)
            self.uid = hashlib.sha256(c.encode("utf-8")).hexdigest()
        except:
            raise ValueError("账号密码错误：" + str(data))


# 正在处理的账号列表
workList = {}
"""
(global) workList ={
    uid: {
        status: pending,
        account: 138xxxxxxxx, 
        password: admin123,
        isAuto: False
        cookie: ""
        SMS_CODE: None,
        msg: "Error Info"
    },
    ...
}
"""
app = Quart(__name__)


def mr(status, **kwargs):
    r_data = {}
    r_data["status"] = status
    for key, value in kwargs.items():
        r_data[str(key)] = value
    r_data = jsonify(r_data)
    r_data.headers["Content-Type"] = "application/json; charset=utf-8"
    return r_data


# -----router-----
@app.route("/", methods=["GET"])
async def index():
    return await send_file('index.html')
# 传入账号密码，启动登录线程
@app.route("/login", methods=["POST"])
async def login():
    print("login")
    data = await request.get_json()
    if "type" not in data:
        data["type"] = "password"
    return loginPublic(data)
    
# 启动登录线程
@app.route("/loginNew", methods=["POST"])
async def loginNew():
    print("loginPassword")
    data = await request.get_json()
    return loginPublic(data)


# 调用后端进行登录
async def THREAD_DO_LOGIN(workList, uid, ocr, ocrDet):
    try:
        await backend.main(workList, uid, ocr, ocrDet)
    except Exception as e:
        print(e)
        workList[uid].msg = str(e)

    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(backend.start(workList, uid))
    except Exception as e:
        print(e)
        workList[uid].msg = str(e)
    """


# 检查后端进度记录
@app.route("/check", methods=["POST"])
async def check():
    data = await request.get_json()
    uid = data.get("uid", None)
    r = None
    # 账号列表有记录
    if workList.get(uid, ""):
        status = workList[uid].status
        if status == "pass":
            cookie = workList[uid].cookie
            r = mr(status, cookie=cookie, msg="成功")
            # 登录成功后保存账户和密码到文件
            account_data = {"account": workList[uid].account, "password": workList[uid].password}
            filename = 'data.json'
            existing_data = load_from_file(filename)
            existing_data.append(account_data)
            save_to_file(filename, existing_data)
        elif status == "pending":
            r = mr(status, msg="正在处理中，请等待")
        elif status == "error":
            r = mr(status, msg="登录失败，请在十秒后重试：" + workList[uid].msg)
        elif status == "SMS":
            r = mr(status, msg="需要短信验证")
        elif status == "wrongSMS":
            r = mr(status, msg="短信验证错误，请重新输入")
        else:
            r = mr("error", msg="笨蛋开发者，忘记适配新状态啦：" + status)
    # 账号列表无记录
    else:
        r = mr("error", msg="未找到该账号记录，请重新登录")
    return r


# 传入短信验证码，更新账号列表使后端可以调用
@app.route("/sms", methods=["POST"])
async def sms():
    data = await request.get_json()
    uid = data.get("uid", None)
    code = data.get("code", None)
    # 检查传入验证码合规
    if len(code) != 6 and not code.isdigit():
        r = mr("wrongSMS", msg="验证码错误")
        return r
    try:
        THREAD_SMS(uid, code)
        r = mr("pass", msg="成功提交验证码")
        return r
    except Exception as e:
        r = mr("error", msg=str(e))
        return r
        
def loginPublic(data):
    try:
        u = account(data)
    except Exception as e:
        r = mr("error", msg=str(e))
        return r
    # 检测重复提交
    if workList.get(u.uid):
        workList[u.uid].SMS_CODE = None
        r = mr("pass", uid=u.uid, msg=f"{u.account}已经在处理了，请稍后再试")
        return r

    # 新增记录
    workList[u.uid] = u
    # 非阻塞启动登录线程
    asyncio.create_task(THREAD_DO_LOGIN(workList, u.uid, ocr, ocrDet))
    # 更新信息，响应api请求
    workList[u.uid].status = "pending"
    r = mr("pass", uid=u.uid, msg=f"{u.account}处理中, 到/check查询处理进度")
    return r

def THREAD_SMS(uid, code):
    print("phase THREAD_SMS: " + str(code))
    u = workList.get(uid, "")
    if not u:
        raise ValueError("账号不在记录中")
    if u.status == "SMS" or u.status == "wrongSMS":
        u.SMS_CODE = code
    else:
        raise ValueError("账号不在SMS过程中")


# -----regular functions-----
# 删除成功或失败的账号记录
async def deleteSession(uid):
    await asyncio.sleep(5)
    del workList[uid]

def load_from_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_to_file(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存到文件时出错: {e}")
"""
@app.route("/delck", methods=["POST"])
def delck():
    data = request.get_json()
    uid = data.get("uid", None)
    if not exist(uid):
        r = mr(False, msg="not exist")
        return r

    THREAD_DELCK(uid)
"""
# 创建本线程的事件循环，运行flask作为第一个任务
asyncio.new_event_loop().run_until_complete(app.run(host=run_host, port=run_port))