const axios = require('axios');
let checkRes = false
let userCookie = null
let ql_host = "https://127.0.0.1:5700"
let ql_app_id = "aaaaa"
let ql_app_screct = "bbbbb"
async function main() {
    const users = await axios.get('https://127.0.0.1:12345/get');
    for (let i = 0; i < users.length; i++) {
        let users_demo = [{ "account": "13133333333", "password": "abcdabcd", "ptpin": "jd_test" }]
    }
    //找青龙的API 获取环境变量后 正则找ptpin一样的 然后进行get_cookie
    let loginRes = await loginApi("13133333333", "abcdabcd")
    await new Promise(resolve => setTimeout(resolve, 2 * 1000));

    if (loginRes) {
        for (let i = 0; i < 30; i++) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            if (!checkRes) {
                await checkApi(loginRes)
            } else {
                //更新
                //return userCookie
            }
        }

    }

}
async function get_cookie(account, password) {

}
async function loginApi(id, pw) {
    let options = {
        url: 'https://127.0.0.1:12345/login',
        headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'GoDongGoCar'
        },
        data: JSON.stringify({
            id, pw
        })
    }
    const { data: loginRes } = await axios.request(options)
    if (loginRes.status == 'pass') {
        return loginRes.uid
    } else {
        return false
    }
}
async function checkApi(uid) {
    let options = {
        url: 'https://127.0.0.1:12345/check',
        headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'GoDongGoCar'
        },
        data: JSON.stringify({
            uid
        })
    }
    const { data: checkRes } = await axios.request(options)
    if (checkRes.status == 'pass') {
        checkRes = true
        userCookie = checkRes.cookie
    } else if (checkRes.status == 'error') {
        checkRes = true
        console.log('error');

    } else if (checkRes.status == 'wrongSMS') {

        checkRes = true
        console.log('wrongSMS');

    } else if (checkRes.status == 'SMS') {
        checkRes = true
        console.log('SMS');
    } else if (checkRes.status == 'pending') {
        checkRes = false

    } else {
        checkRes = true
        console.log('error' + checkRes.msg);
    }
}