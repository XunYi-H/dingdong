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
let input = "";

function main() {
    try {
        let account = "";
        let password = "";
        let code = "";
        promptInput("手机号", (input) => !isNaN(input));

        if (!input) return exitWithMessage("超时/已退出");
        account = input;
        promptInput("密码", (input) => input !== "");
        if (!input) return exitWithMessage("超时/已退出");
        password = input;
        const loginResponse = loginApi(account + "", password);
        if (!loginResponse || loginResponse.status !== "pass") return;

        s.reply(`${qq}#${s.getUserName()} 正在执行登录，请稍等`);
        for (let t = 0; t < 20; t++) {
            time.sleep(1000);
            const checkResponse = checkApi(loginResponse.uid);
            s.reply(checkResponse.msg);
            if (checkResponse.status === "pass") {
                s.reply(`${qq}#${s.getUserName()} 登录成功`);
                //拿到COOKIE
                return;
            } else if (checkResponse.status === "SMS") {
                s.reply(`${qq}#${s.getUserName()} 正在发送短信，请稍等`);
                promptInput("短信验证码", (input) => !isNaN(input));
                if (!input) return exitWithMessage("超时/已退出");
                code = input;
                let smsResponse = smsApi(loginResponse.uid, code + "");
                if (smsResponse.status === "wrongSMS") {
                    s.reply(`${qq}#${s.getUserName()} 短信验证码错误`);
                    promptInput("短信验证码", (input) => !isNaN(input));
                    if (!input) return exitWithMessage("超时/已退出");
                    code = input;
                    smsResponse = smsApi(loginResponse.uid, code + "");
                    if (smsResponse.status === "pass") {
                        s.reply(`${qq}#${s.getUserName()} 短信验证码正确`);
                        const checkResponse = checkApi(loginResponse.uid);
                        if (checkResponse.status === "pass") {
                            s.reply(`${qq}#${s.getUserName()} 登录成功`);
                            //拿到COOKIE
                            return;
                        }
                    }
                }
                if (smsResponse.status === "pass") {
                    s.reply(`${qq}#${s.getUserName()} 短信验证码正确`);
                    const checkResponse = checkApi(loginResponse.uid);

                    if (checkResponse.status === "pass") {
                        s.reply(`${qq}#${s.getUserName()} 登录成功`);
                        //拿到COOKIE
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

function exitWithMessage(message) {
    s.reply(message);
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
//进行更新上传操作
main();
