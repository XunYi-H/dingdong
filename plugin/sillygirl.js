/**
 * @title JDCK
 * @author smallfawn
 * @version v1.0.0
 * @rule 叮叮当
 */

const s = sender;
const chat = s.getChatId();
const qq = s.getUserId();
const inputTimeout = 30 * 1000;
const host = "http://8.141.174.247:12345";
const bucket = Bucket("smallfawn");
let input = "";

function main() {
    try {
        if (!bucket["ptpins"]) {
            bucket["ptpins"] = [].toString();
        }
        let ptpins = bucket["ptpins"];
        try {
            ptpins = JSON.parse(ptpins);
        } catch (error) {
            s.reply(`存储桶解析失败`);
            return;
        }

        let account = "";
        let password = "";
        let code = "";
        promptInput("手机号", (input) => !isNaN(input));
        if (!input) return s.reply("超时/已退出");
        account = input;
        promptInput("密码", (input) => input !== "");
        if (!input) return s.reply("超时/已退出");
        password = input;
        const loginResponse = loginApi(account + "", password);
        if (!loginResponse || loginResponse.status !== "pass") return;

        s.reply(`${qq}#${s.getUserName()} 正在执行登录，请稍等`);
        for (let t = 0; t < 20; t++) {
            time.sleep(1000);
            const checkResponse = checkApi(loginResponse.uid);
            if (checkResponse.status === "pass") {
                s.reply(`${qq}#${s.getUserName()} 登录成功`);
                let ptpinValue = checkResponse.cookie.match(/pt_pin=([^; ]+)(?=;?)/)[1];
                ptpins.push({ ptpin: ptpinValue, account, password });
                bucket["ptpins"] = JSON.stringify(ptpins);
                return;
            } else if (checkResponse.status === "SMS") {
                s.reply(`${qq}#${s.getUserName()} 正在发送短信，请稍等`);
                promptInput("短信验证码", (input) => !isNaN(input));
                if (!input) return s.reply("超时/已退出");
                code = input;
                let smsResponse = smsApi(loginResponse.uid, code + "");
                if (smsResponse.status === "wrongSMS") {
                    s.reply(`${qq}#${s.getUserName()} 短信验证码错误`);
                    promptInput("短信验证码", (input) => !isNaN(input));
                    if (!input) return s.reply("超时/已退出");
                    code = input;
                    smsResponse = smsApi(loginResponse.uid, code + "");
                    if (smsResponse.status === "pass") {
                        s.reply(`${qq}#${s.getUserName()} 短信验证码正确`);
                        const checkResponse = checkApi(loginResponse.uid);
                        if (checkResponse.status === "pass") {
                            s.reply(`${qq}#${s.getUserName()} 登录成功`);
                            let ptpinValue = checkResponse.cookie.match(
                                /pt_pin=([^; ]+)(?=;?)/
                            )[1];
                            ptpins.push({ ptpin: ptpinValue, account, password });
                            bucket["ptpins"] = JSON.stringify(ptpins);
                            return;
                        }
                    }
                }
                if (smsResponse.status === "pass") {
                    s.reply(`${qq}#${s.getUserName()} 短信验证码正确`);
                    const checkResponse = checkApi(loginResponse.uid);
                    if (checkResponse.status === "pass") {
                        s.reply(`${qq}#${s.getUserName()} 登录成功`);
                        return;
                    }
                }
            } else if (checkResponse.status === "error") {
                s.reply(`${qq}#${s.getUserName()}` + checkResponse.msg);
                return;
            }
        }
    } catch (error) {
        s.reply(`操作失败：${error.message}`);
    }
}

function promptInput(promptText, validationFunction) {
    s.reply(
        `@${qq}#${s.getUserName()} 请在 ${inputTimeout / 1000
        }s 内输入正确的 ${promptText}`
    );
    s.listen({
        handle: (s) => {
            input = s.getContent();
            if (validationFunction(input) && isSameUserAndChat()) {
                s.reply(`@${qq}#${s.getUserName()} 输入正确 ` + input);
                return;
            } else if (input === "q" && isSameUserAndChat()) {
                input = "";
                return;
            } else {
                input = "";
                return;
            }
        },
        timeout: inputTimeout,
    });
}

function isSameUserAndChat() {
    return s.getUserId() === qq && s.getChatId() === chat;
}

function loginApi(account, password) {
    const response = request({
        url: `${host}/login`,
        method: "post",
        json: true,
        body: { id: account, pw: password },
    });
    return response.body;
}

function checkApi(uid) {
    const response = request({
        url: `${host}/check`,
        method: "post",
        json: true,
        body: { uid: uid },
    });
    return response.body;
}

function smsApi(uid, code) {
    const response = request({
        url: `${host}/sms`,
        method: "post",
        json: true,
        body: { uid: uid, code: code },
    });
    return response.body;
}
//根据存储桶拿到青龙密钥
function isValidUrl(url) {
    const pattern = /^(https?:\/\/)[^\s/$.?#].[^\s]*\.[^\s]*$/i;
    return pattern.test(url);
}
//进行更新上传操作
function update(cookies) {
    let ql_host = bucket["ql_host"];
    let ql_app_id = bucket["ql_app_id"];
    let ql_app_secret = bucket["ql_app_secret"];
    if (!ql_app_id || !ql_app_secret || !ql_host) {
        s.reply(`请先配置青龙密钥和APPID和青龙地址`);
        return;
    }
    if (!isValidUrl(ql_host)) {
        s.reply(`青龙地址格式错误`);
        return;
    }
    let token = request({
        url: `${ql_host}/open/auth/token?client_id=${ql_app_id}&client_secret=${ql_app_secret}`,
        method: "post",
        json: true,
    }).body.data.token;
    let env = request({
        url: `${ql_host}/open/envs?t=${Date.now()}&searchValue=JD_COOKIE`,
        method: "get",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        json: true,
    }).body.data;
    if (env.length == 0) {
    } else {
        for (let i = 0; i < env.length; i++) {
            if (env[i].name == "JD_COOKIE") {
                if (
                    env[i].value.match(/pt_pin=([^; ]+)(?=;?)/) &&
                    env[i].value.match(/pt_pin=([^; ]+)(?=;?)/)[1] == cookies.match(/pt_pin=([^; ]+)(?=;?)/)[1]
                ) {
                    let id = env[i].id;
                    let updateRes = request({
                        url: `${ql_host}/open/envs?t=${Date.now()}`,
                        method: "post",
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                        json: true,
                        body: { "name": "JD_COOKIE", "value": "VASASSS", "remarks": null, "id": id }
                    }).body.code
                    if (updateRes == 200) {
                        s.reply(`更新成功`);
                    }
                }
            }
        }
    }
}
main();
