const axios = require('axios');
let checkRes = false
let userCookie = null
let ql_host = "https://127.0.0.1:5700"
let GoDongGoCarHost = "http://127.0.0.1:12345"
let ql_app_id = "aaaaa"
let ql_app_screct = "bbbbb"
let ql_isNewVersion = true //是否为青龙新版本（ >=2.11 ）
let failEnvs = []
let waitUpEnvs = [] //匹配成功待更新
async function main() {
    let QL = new QLAPI()
    let token = await QL.getToken()
    if (token) {
        await QL.checkCookie()
        if (failEnvs.length > 0) {
            const users = await axios.get(`${GoDongGoCarHost}/get`);
            for (let i of failEnvs) {

                let ap = users.find(
                    (item) => {
                        if (item.ptpin == i['ptpin']) {
                            item['id'] = i['id']
                            return item
                        }
                    }
                )
                if (ap) {
                    waitUpEnvs.push(ap)
                }
            }
        }
        if (waitUpEnvs.length > 0) {
            for (let i of waitUpEnvs) {
                let loginRes = await loginApi(i['account'], i['password'])
                console.log(`等待2s`);
                await new Promise(resolve => setTimeout(resolve, 2 * 1000));
                if (loginRes) {
                    for (let j = 0; j < 30; j++) {
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        if (!checkRes) {
                            await checkApi(loginRes)
                        } else if (userCookie) {
                            await QL.updateEnv(i['id'], userCookie)
                        } else {
                            console.log(`账号${i['account']}登录失败`);
                        }
                    }

                }
            }
        }
    }




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
        }),
        method: 'POST'
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
        }),
        method: 'POST'
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
function getPin(cookie) {
    const match = cookie.match(/pt_pin=([^; ]+)(?=;?)/);
    if (match) {
        return match[1];
    }
    return '';
}
class QLAPI {
    constructor() {
        this.ql_host = ql_host
        this.ql_app_id = ql_app_id
        this.ql_app_screct = ql_app_screct
        this.qlenvs = []
        this.ql_token = ''
        this.ql_isNewVersion = ql_isNewVersion
    }
    async getToken() {
        let options = {
            url: `${this.ql_host}/open/auth/token?client_id=${this.ql_app_id}&client_secret=${this.ql_app_screct}`,
            method: 'GET'
        }
        const { data: tokenRes } = await axios.request(options)
        if (tokenRes.code == 200) {
            return tokenRes.data.token
        } else {
            return false
        }
    }
    async updateEnv(id, cookie) {
        let options
        if (this.ql_isNewVersion) {
            options = {
                url: `${this.ql_host}/open/envs?t=${new Date().getTime()}`,
                method: "put",
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${this.ql_token}`,
                },
                data: JSON.stringify({ "name": "JD_COOKIE", "value": cookie, "id": id })
            }
        } else {
            options = {
                url: `${this.ql_host}/open/envs?t=${new Date().getTime()}`,
                method: "put",
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${this.ql_token}`,
                },
                data: JSON.stringify({ "name": "JD_COOKIE", "value": cookie, "_id": id })
            }
        }
        const { data: updateRes } = await axios.request(options)
        if (updateRes.code == 200) {
            return true
        } else {
            return false
        }
    }
    async createEnv(value) {
        let options = {
            url: `${this.ql_host}/open/envs?t=${new Date().getTime()}`,
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${this.ql_token}`,
            },
            data: JSON.stringify([{ "value": value, "name": 'JD_COOKIE' }])
        }
        const { data: updateRes } = await axios.request(options)
        if (updateRes.code == 200) {
            return true
        } else {
            return false
        }
    }
    async checkCookie() {
        let envs = await this.getEnvs('JD_COOKIE')
        if (this.ql_isNewVersion) {
            for (let i of envs) {
                if (i['status'] == 1) {
                    let cookie = i['value']
                    let id = i['id']
                    failEnvs.push({ id: id, ptpin: getPin(cookie) })
                }
            }
        } else {
            for (let i of envs) {
                if (i['status'] == 1) {
                    let cookie = i['value']
                    let id = i['_id']
                    failEnvs.push({ id: id, ptpin: getPin(cookie) })
                }
            }
        }
    }
    async getEnvs() {
        let options = {
            url: `${this.ql_host}/open/envs?t=${new Date().getTime()}&&searchValue=JD_COOKIE`,
            method: "GET",
            headers: {
                Authorization: `Bearer ${this.ql_token}`,
            },
        }
        const { data: tokenRes } = await axios.request(options)
        if (tokenRes.code == 200) {
            return tokenRes.data
        } else {
            return false
        }
    }
} 