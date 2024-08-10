//定时0 0 6 * * *
//根据存储桶拿到青龙配置文件
let bucket = Bucket('smallfawn')
let qlappid = bucket['ql_app_id']
let qlappsecret = bucket['ql_app_secret']
//计划将ptpin列表改为数组
let demo = [{ ptpin: "ptpin", password: "password", account: "account" }]
/**
 * 获取临时Token
 */
function getToken() {
}
/**
 * 获取青龙环境
 */
function getEnv() {

}
/**
 * 检索失效的京东COOKIE
 */
function checkEnv() {

}
//请求获得失效的京东COOKIE
//匹配pt_pin //根据存储桶拿到pt_pin 相关的手机号和密码

function getAccountAndPassword(ptpin) {
    //return bucket[ptpin]
}
//再次请求登录
function login(account, password) {
    account = account + ''
    password = password + ''
}
function updateEnv() {

}
//更新青龙
