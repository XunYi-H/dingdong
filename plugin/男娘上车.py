# [disable:false]
# [title:男娘撸豆豆]
# [author: 大帅逼]
# [class: 工具类]
# [platform: qq,wx,tg,tb]
# [rule: ^男娘(.*)$]
'''
未测试，看接口写的
奥特曼插件

'''
import middleware,requests,re



class JD:
    def __init__(self, user, sender):
        self.user = user
        self.sender = sender
        self.tongname = ""#桶名
        self.tongconfig = ""#桶配置
        self.host = "http://127.0.0.1:12345"#middleware.bucketGet(self.tongconfig,"host")

    def get_ck(self):
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
                #开始登录login
                loginData = self.login(phone,password)
                if loginData:
                    if loginData["status"] != "pass":
                        self.sender.reply(f"错误退出：{loginData}")
                        exit()
                    else:
                        self.sender.reply(f"{phone[:3]}***{phone[7:]}正在登录中...")
                        uid = loginData["uid"]
                        #check,获取cookie
                        checkData = self.check(uid)
                        if checkData:
                            if checkData["status"] == "pass":
                                #无验证
                                cookie = checkData["cookie"]
                                self.sender.reply(f"获取cookie成功：{cookie}")
                                #调用青龙
                                #QL(cookie)



                            elif checkData["status"] == "SMS":
                                #进行验证
                                self.sender.reply(f"{checkData['msg']},已发送短信")
                                code = self.sender.listen(180000)#等待3分钟
                                if code == "q" or code is None:
                                    self.sender.reply("验证失败")
                                    return
                                else:
                                    #验证码
                                    smsData = self.sms(uid,code)
                                    if smsData:
                                        if smsData["status"] == "pass":
                                            #成功
                                            checkData = self.check(uid)
                                            if checkData:
                                                if checkData["status"] == "pass":
                                                    # 无验证
                                                    cookie = checkData["cookie"]
                                                    self.sender.reply(f"获取cookie成功：{cookie}")
                                                    # 调用青龙
                                                    # QL(cookie)
                                                    return
                                                else:
                                                    self.sender.reply(f"重新登录吧：{checkData}")
                                                    return
                                            else:
                                                self.sender.reply("服务错误")


                                        else:
                                            #验证码错误
                                            self.sender.reply(f"{smsData['msg']}")
                                            return
                                    else:
                                        self.sender.reply("服务错误")

                            else:
                                self.sender.reply(f"{checkData['msg']}")
                                exit(0)

                        else:
                            self.sender.reply("服务错误")


                else:
                    self.sender.reply("服务错误")

        else:
            self.sender.reply("手机号错误")


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
# class QL:
#     def __init__(self,ck):
#         self.ck = ck
#         self.qlhost = ""
#         self.qlid = ""
#         self.qlsecret = ""
#         self.qltoken = None
#         self.qlhd = None
#     def ql_login(self):
#         url = f"{self.qlhost}/open/auth/token?client_id={self.qlid}&client_secret={self.qlsecret}"
#         res = requests.get(url).json()
#         if res["code"] == 200:
#             self.qltoken = res['data']['token']
#             self.qlhd = {
#                 "Authorization": f"Bearer {self.qltoken}",
#                 "accept": "application/json",
#                 "Content-Type": "application/json",
#             }
#             return True
#         else:  
#             return False
#     def get_env(self):
#         return 
#     def update_env(self):
#         return 
#     def set_env(self):
#         return 
    





if __name__ == "__main__":
    senderID = middleware.getSenderID()
    sender = middleware.Sender(senderID)
    user = sender.getUserID()
    JD = JD(user, sender)
    message = sender.getMessage()
    if "男娘涩涩" == message:
        JD.get_ck()
