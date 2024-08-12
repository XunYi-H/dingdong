const axios = require('axios');

const ql_host = "http://127.0.0.1:5700";
const GoDongGoCarHost = "http://127.0.0.1:12345";
const ql_app_id = "aaaaa";
const ql_app_secret = "bbbbb";
const ql_isNewVersion = true; // 是否为青龙新版本（>= 2.11）
const key = 'AAAAA';

let checkRes = false;
let userCookie = null;
let failEnvs = [];
let waitUpEnvs = [];

async function main() {
    const QL = new QLAPI();

    const token = await QL.getToken();
    if (!token) return;

    await QL.checkCookie();

    if (failEnvs.length > 0) {
        const { data: users } = await axios.get(`${GoDongGoCarHost}/get?k=${key}`);

        failEnvs.forEach(env => {
            const matchedUser = users.find(user => user.ptpin === env.ptpin);
            if (matchedUser) {
                matchedUser.id = env.id;
                waitUpEnvs.push(matchedUser);
            }
        });
    }

    for (const user of waitUpEnvs) {
        const loginRes = await loginApi(user.account, user.password);
        if (loginRes) {
            await handleLoginResponse(loginRes, user, QL);
        } else {
            console.log(`账号 ${user.account} 登录失败`);
        }
    }
}

async function loginApi(id, pw) {
    const options = {
        url: `${GoDongGoCarHost}/login`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'GoDongGoCar',
        },
        data: { id, pw },
    };

    const { data: loginRes } = await axios(options);

    return loginRes.status === 'pass' ? loginRes.uid : false;
}

async function checkApi(uid) {
    const options = {
        url: `${GoDongGoCarHost}/check`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'GoDongGoCar',
        },
        data: { uid },
    };

    const { data: checkResData } = await axios(options);
    checkRes = true;

    switch (checkResData.status) {
        case 'pass':
            userCookie = checkResData.cookie;
            break;
        case 'error':
            console.log('Error occurred');
            break;
        case 'wrongSMS':
            console.log('Wrong SMS');
            break;
        case 'SMS':
            console.log('SMS required');
            break;
        case 'pending':
            checkRes = false;
            break;
        default:
            console.log(`Error: ${checkResData.msg}`);
    }
}

async function handleLoginResponse(loginRes, user, QL) {
    console.log('等待 2s');
    await delay(2000);

    for (let i = 0; i < 30; i++) {
        await delay(1000);

        if (!checkRes) {
            await checkApi(loginRes);
        } else if (userCookie) {
            await QL.updateEnv(user.id, userCookie);
            break;
        } else {
            console.log(`账号 ${user.account} 登录失败`);
            break;
        }
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getPin(cookie) {
    const match = cookie.match(/pt_pin=([^; ]+)(?=;?)/);
    return match ? match[1] : '';
}

class QLAPI {
    constructor() {
        this.ql_host = ql_host;
        this.ql_app_id = ql_app_id;
        this.ql_app_secret = ql_app_secret;
        this.ql_isNewVersion = ql_isNewVersion;
        this.ql_token = '';
    }

    async getToken() {
        const options = {
            url: `${this.ql_host}/open/auth/token?client_id=${this.ql_app_id}&client_secret=${this.ql_app_secret}`,
            method: 'GET',
        };

        const { data: tokenRes } = await axios(options);
        if (tokenRes.code === 200) {
            this.ql_token = tokenRes.data.token;
            return this.ql_token;
        }
        return false;
    }

    async updateEnv(id, cookie) {
        const options = {
            url: `${this.ql_host}/open/envs?t=${Date.now()}`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${this.ql_token}`,
            },
            data: JSON.stringify({ "name": "JD_COOKIE", "value": cookie, "id": id }),
        };

        const { data: updateRes } = await axios(options);
        return updateRes.code === 200;
    }

    async checkCookie() {
        const envs = await this.getEnvs();
        envs.forEach(env => {
            if (env.status === 1) {
                const id = this.ql_isNewVersion ? env.id : env._id;
                const ptpin = getPin(env.value);
                failEnvs.push({ id, ptpin });
            }
        });
    }

    async getEnvs() {
        const options = {
            url: `${this.ql_host}/open/envs?t=${Date.now()}&searchValue=JD_COOKIE`,
            method: 'GET',
            headers: {
                Authorization: `Bearer ${this.ql_token}`,
            },
        };

        const { data: envRes } = await axios(options);
        return envRes.code === 200 ? envRes.data : [];
    }
}

main().catch(console.error);
