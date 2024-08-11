# [disable:false]
# [title:男娘撸豆豆]
# [author: 大帅逼]
# [class: 工具类]
# [platform: qq,wx,tg,tb]
# [rule: ^男娘(.*)$]
# [param: {"required":true,"key":"JDConfig.ql_data","bool":false,"placeholder":"青龙配置","name":"青龙配置","desc":"青龙地址#client_id#client_secret,例如：https://1.1.1:5700#123#456"}]
# [param: {"required":true,"key":"JDConfig.host","bool":false,"placeholder":"","name":"滑块接口","desc":"滑块接口ip:端口"}]


'''
未测试，看接口写的
奥特曼插件，首先填好插件配置
bug肯定有，看着改

不是完整插件，没有定时更新ck，只是测试账号密码正常获取ck，提交青龙，同时保存到奥特曼
'''
import time
import middleware,requests,re



class JD:
    def __init__(self, user, sender):
        self.user = user
        self.sender = sender
        self.tongname = "JD_login"#桶名
        self.tongconfig = "JDConfig"#桶配置
        self.host = middleware.bucketGet(self.tongconfig,"host")
        if self.host == "":
            self.sender.reply("没有填写过滑块接口")
            exit(0)


    def get_ck(self):

        tong = middleware.bucketGet(self.tongname, self.user)
        if tong == "" or tong == "[]":
            if tong == "[]":
                middleware.bucketDel(self.tongname, self.user)
            self.sender.reply("输入手机号")
            phone = self.sender.listen(180000)
            if phone == "" or phone == "q":
                self.sender.reply("退出")
                exit()
            elif re.compile(r'^1[3-9]\d{9}$').match(phone):
                self.sender.reply("输入密码")
                password = self.sender.listen(180000)
                if password == "" or password == "q":
                    self.sender.reply("退出")
                    exit()
                else:
                    self.l(phone,password)
            else:
                self.sender.reply("手机号错误")
        else:
            msg = ""
            tong = eval(tong)
            n = 0
            for i in tong:
                n += 1
                phone = f'{i.split("#")[0][:3]}***{i.split("#")[0][:7]}'
                msg += f"[{n}]:{phone}\n"
            self.sender.reply("选择账号序号获取cookie")
            xh = self.sender.listen(180000)
            if xh == "" or xh == "q":
                self.sender.reply("退出")
                exit()
            elif int(xh)-1 <= len(tong):
                phone = tong[int(xh)-1].split("#")[0]
                password = tong[int(xh)-1].split("#")[1]
                self.l(phone,password)
            else:
                self.sender.reply("错误退出")
                exit()

    def l(self,phone,password):

        # 开始登录login
        loginData = self.login(phone, password)
        if loginData:
            if loginData["status"] != "pass":
                self.sender.reply(f"错误退出：{loginData}")
                exit()
            else:
                self.sender.reply(f"{phone[:3]}***{phone[7:]}正在登录中...")
                uid = loginData["uid"]
                # check,获取cookie
                for t in range(20):
                    checkData = self.check(uid)
                    if checkData:
                        if checkData["status"] == "pass":
                            # 无验证
                            cookie = checkData["cookie"]
                            self.sender.reply(f"获取cookie成功：{cookie}")
                            # 调用青龙
                            qlData = QL(cookie, user, sender).put_ql()
                            self.sender.reply(qlData)

                            # 存储账号密码到奥特曼桶
                            tong = middleware.bucketGet(self.tongname, self.user)
                            if tong == "":
                                old = [f"{phone}#{password}"]
                                middleware.bucketSet(self.tongname, self.user, f"{old}")
                            else:
                                tong = eval(tong)
                                a = 0
                                for z in tong:
                                    if phone == z.split("#")[0]:
                                        tong[a] = f"{phone}#{password}"
                                        middleware.bucketSet(self.tongname, self.user, f"{tong}")
                                        return
                                    a += 1

                                tong.append(f"{phone}#{password}")
                                middleware.bucketSet(self.tongname, self.user, f"{tong}")
                                return

                            break



                        elif checkData["status"] == "SMS":
                            # 进行验证
                            self.sender.reply(f"{checkData['msg']},已发送短信")
                            code = self.sender.listen(180000)  # 等待3分钟
                            if code == "q" or code is None:
                                self.sender.reply("验证失败")
                                return
                            else:
                                # 验证码
                                smsData = self.sms(uid, code)
                                if smsData:
                                    if smsData["status"] == "pass":
                                        # 成功
                                        for i in range(20):
                                            checkData = self.check(uid)
                                            if checkData:
                                                if checkData["status"] == "pass":
                                                    # 无验证
                                                    cookie = checkData["cookie"]
                                                    self.sender.reply(f"获取cookie成功：{cookie}")
                                                    # 调用青龙
                                                    qlData = QL(cookie, user, sender).put_ql()
                                                    self.sender.reply(qlData)
                                                    # 存储账号密码到奥特曼桶
                                                    tong = middleware.bucketGet(self.tongname, self.user)
                                                    if tong == "":
                                                        old = [f"{phone}#{password}"]
                                                        middleware.bucketSet(self.tongname, self.user, f"{old}")
                                                        return
                                                    else:
                                                        tong = eval(tong)
                                                        a = 0
                                                        for z in tong:
                                                            if phone == z.split("#")[0]:
                                                                tong[a] = f"{phone}#{password}"
                                                                middleware.bucketSet(self.tongname, self.user,
                                                                                     f"{tong}")
                                                                return
                                                            a += 1

                                                        tong.append(f"{phone}#{password}")
                                                        middleware.bucketSet(self.tongname, self.user,
                                                                             f"{tong}")
                                                        return




                                                else:
                                                    self.sender.reply(f"重新登录吧：{checkData}")
                                                    return
                                            elif checkData["status"] == "pending":
                                                time.sleep(1)
                                                continue
                                            else:
                                                self.sender.reply(f"{checkData['msg']}")
                                                return
                                        self.sender.reply("验证超时")
                                        exit(0)



                                    else:
                                        # 验证码错误
                                        self.sender.reply(f"{smsData['msg']}")
                                        return
                                else:
                                    self.sender.reply("服务错误")
                                    return
                        elif checkData["status"] == "pending":
                            time.sleep(1)
                            continue
                        else:
                            self.sender.reply(f"{checkData['msg']}")
                            return
                        self.sender.reply("验证超时")
                        exit(0)


                    else:
                        self.sender.reply("服务错误")
                    time.sleep(1)
                self.sender.reply("验证超时")
                exit(0)
        else:
            self.sender.reply("服务错误")



    def login(self,phone,pd):
        res = requests.post(f"{self.host}/login",json={"id":phone,"password":pd})
        if res.status_code == 200:
            return res.json()
        else:
            return False

    def check(self,uid):
        res = requests.post(f"{self.host}/check", json={"uid": uid})
        if res.status_code == 200:
            return res.json()
        else:
            return False
    def sms(self,uid,code):
        res = requests.post(f"{self.host}/sms", json={"uid": uid,"code":code})
        if res.status_code == 200:
            return res.json()
        else:
            return False
# 青龙函数例子
class QL:
    def __init__(self,ck, user, sender):
        self.user = user
        self.sender = sender
        self.ck = ck
        ql_data = middleware.bucketGet("JDConfig","ql_data")
        if ql_data == "":
            self.qlhost = ql_data.split("#")[0]
            self.qlid = ql_data.split("#")[1]
            self.qlsecret = ql_data.split("#")[2]
        else:
            self.qlhost = ""
            self.qlid = ""
            self.qlsecret = ""
        self.qltoken = None
        self.qlhd = None
        self.pin = re.search(r'pt_pin=([^;]+)',ck).group(1)
        self.qlblm = "JD_COOKIE"
    def ql_login(self):
        url = f"{self.qlhost}/open/auth/token?client_id={self.qlid}&client_secret={self.qlsecret}"
        res = requests.get(url).json()
        if res["code"] == 200:
            self.qltoken = res['data']['token']
            self.qlhd = {
                "Authorization": f"Bearer {self.qltoken}",
                "accept": "application/json",
                "Content-Type": "application/json",
            }
            return True
        else:
            return False
    def get_env(self):
        url = f'{self.qlhost}/open/envs'
        r = requests.get(url, headers=self.qlhd)
        code = r.json()['code']
        if code == 200:
            data = r.json()['data']
            for i in data:
                remarks = i.get('remarks')
                if remarks is None:
                    remarks = []
                if i['name'] == self.qlblm and self.pin in remarks or self.pin in i['value']:
                    self.envs_id = i['id']
                    self.status = i['status']
                    return True
                else:
                    continue
            return False
        else:
            return False
    def update_env(self):
        url = f'{self.qlhost}/open/envs'
        data = {
            "value": f"{self.ck}",
            "name": f'{self.qlblm}',
            "remarks": f"{self.pin}",
            'id': self.envs_id
        }
        r = requests.put(url, headers=self.qlhd, json=data)
        code = r.json()['code']
        if code == 200:
            return True
        else:
            return False
    def set_env(self):
        url = f'{self.qlhost}/open/envs'
        data = [
            {
                "value": f"{self.ck}",
                "name": f'{self.qlblm}',
                "remarks": f"{self.pin}"
            }
        ]
        r = requests.post(url, headers=self.qlhd, json=data)
        code = r.json()['code']
        if code == 200:
            return True
        else:
            return False
    def qy_env(self):
        """启用/禁用环境变量"""
        try:
            url = f"{self.qlhost}/open/envs/enable"
            res = requests.put(url, headers=self.qlhd, json=[self.envs_id]).status_code
            if res == 200:
                return True
            else:
                return False

        except requests.exceptions.RequestException as e:
            return False

    def jyEnv(self):
        url = f"{self.qlhost}/open/envs/disable"
        res = requests.put(url, headers=self.qlhd, json=[self.envs_id]).status_code
        if res == 200:
            return True
        else:
            return False
    def put_ql(self):
        from datetime import datetime
        if self.qlhost == "":
            return "没有配置青龙桶数据"
        if self.ql_login():
            if self.get_env():
                if self.update_env():
                    if self.status == 1:
                        self.qy_env()
                        qd = self.sender.getImtype().upper()  # 获取渠道
                        # 保存渠道
                        middleware.bucketSet(f"pin{qd}", self.pin, self.user)
                        # notify，保存通知
                        value = {"ID": self.pin, "Pet": False, "Fruit": False, "DreamFactory": False, "Note": "",
                                 "PtKey": re.search(r"pt_key=([^;]+)", self.ck).group(1), "AssetCron": "",
                                 "PushPlus": "",
                                 "LoginedAt": datetime.now(), "ClientID": self.qlid}
                        middleware.bucketSet(f"jdNotify", self.pin, f"{value}")
                    return "更新ck成功"
                else:
                    return "更新ck出现错误"
            else:
                if self.set_env():
                    qd = self.sender.getImtype().upper()  # 获取渠道
                    # 保存渠道
                    middleware.bucketSet(f"pin{qd}", self.pin, self.user)
                    # notify，保存通知
                    value = {"ID": self.pin, "Pet": False, "Fruit": False, "DreamFactory": False, "Note": "",
                             "PtKey": re.search(r"pt_key=([^;]+)", self.ck).group(1), "AssetCron": "", "PushPlus": "",
                             "LoginedAt": datetime.now(), "ClientID": self.qlid}
                    middleware.bucketSet(f"jdNotify", self.pin, f"{value}")
                    return "提交ck成功"
                else:
                    return "提交ck出现错误"
        else:
            return "青龙连接失败"







if __name__ == "__main__":
    senderID = middleware.getSenderID()
    sender = middleware.Sender(senderID)
    user = sender.getUserID()
    JD = JD(user, sender)
    message = sender.getMessage()
    if "男娘涩涩" == message:
        JD.get_ck()
