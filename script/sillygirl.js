//定时0 0 6 * * *
//根据存储桶拿到青龙配置文件
let bucket = Bucket("smallfawn");
let qlappid = bucket["ql_app_id"];
let qlappsecret = bucket["ql_app_secret"];
let ptpins = bucket["ptpins"];
let qlhost = bucket["ql_host"];
let jdckhost = bucket["jdck_host"];
let failEnv = [];//初始化失败的环境变量
let token = "";
let env = []
/**
 * 获取临时Token
 */
function getToken() {
    let { body: tokenRes } = request({
        url: `${ql_host}/open/auth/token?client_id=${ql_app_id}&client_secret=${ql_app_secret}`,
        method: "get",
        json: true,
    })
    if (tokenRes.code != 200) {
        console.log(`青龙密钥错误`);
        return;
    } else {
        token = tokenRes.data.token;
    }
}
/**
 * 获取青龙环境
 */
function getEnv() {
    let { body: envRes } = request({
        url: `${ql_host}/open/envs?t=${new Date().getTime()}&&searchValue=JD_COOKIE`,
        method: "get",
        headers: {
            Authorization: `Bearer ${token}`,
        },
        json: true,
    })
    if (envRes.code != 200) {
        console.log(`青龙环境获取失败`);
        return;
    } else {
        env = envRes.data;
        console.log(`青龙环境获取成功`);
    }
}
/**
 * 检索失效的京东COOKIE
 */
function checkEnv(env) {
    for (let i = 0; i < env.length; i++) {
        if (env[i].name == "JD_COOKIE") {
            if (
                env[i].value.match(/pt_pin=([^; ]+)(?=;?)/)
            ) {
                if (env[i].status == 1) {
                    //无效
                    failEnv.push(env[i].value.match(/pt_pin=([^; ]+)(?=;?)/)[1]);
                }
            }
        }
    }
}
//请求获得失效的京东COOKIE
//匹配pt_pin //根据存储桶拿到pt_pin 相关的手机号和密码


//再次请求登录
//理论上第一次需要经过短信验证 这里在用户第一次提交账号密码时就已经通过了
function login(account, password) {
    account = account + "";
    password = password + "";
    const response = request({
        url: `${jdckhost}/login`,
        method: "post",
        json: true,
        body: { id: account, pw: password },
    });
    if (response.body.status == 'pass') {
        for (let i = 0; i < 15; i++) {
            time.sleep(1000)
            let checkRes = request({
                url: `${host}/check`,
                method: "post",
                json: true,
                body: { uid: response.body.uid },
            });
            if (checkRes.body.status == 'pass') {
                return response.body.cookie
            }
        }

    } else {
        const response = request({
            url: `${host}/login`,
            method: "post",
            json: true,
            body: { id: account, pw: password },
        });
        if (response.body.status == 'pass') {
            for (let i = 0; i < 15; i++) {
                time.sleep(1000)
                let checkRes = request({
                    url: `${host}/check`,
                    method: "post",
                    json: true,
                    body: { uid: response.body.uid },
                });
                if (checkRes.body.status == 'pass') {
                    return response.body.cookie
                }
            }
        } else {
            return ''
        }
    }
}
function updateEnv() {

 }
//更新青龙
function main() {
    try {
        ptpins = JSON.parse(ptpins);
    } catch (error) {
        console.log(`存储桶解析失败`);
        return;
    }
    getToken();
    if (token !== '') {
        getEnv();
        checkEnv();
        for (let i = 0; i < ptpins.length; i++) {
            for (let j = 0; j < failEnv.length; j++) {
                if (ptpins[i].ptpin == failEnv[j]) {
                    let account = ptpins[i].account;
                    let password = ptpins[i].password;
                    let cookie = login(account, password);
                    if (cookie != '') {
                        //更新青龙
                        //应该更新完毕之后 再去启动变量
                        //未完待续
                        updateEnv(cookie);
                    }
                }
            }
        }
    }

    //...
}
