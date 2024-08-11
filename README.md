# 请合作者完善plugin 里面的两个机器人框架的插件 和script机器人定时执行脚本
# 目前计划适配 无界 傻妞 奥特曼
# 截至8-17 未参与issues 提议(反馈BUG和功能建议) 和 pr代码(提供和优化代码)的都会被撤去内测资格
【闲鱼】https://m.tb.cn/h.gl6rDES?tk=L4Fe33wtKth CZ0015 「我在闲鱼发布了【爱国者sata3.0 256g（2.5寸）S500读500m】」
点击链接直接打开
```shell
docker run -d -p 12345:12345 registry.cn-hangzhou.aliyuncs.com/smallfawn/ddd
```
```shell
docker run -dit \
  -v $PWD/godonggocar/config.json:/config.json \
  -p 12345:12345 \
registry.cn-hangzhou.aliyuncs.com/smallfawn/ddd
```
第一个12345是外部接口
## `/login` 接口

### 描述
处理登录请求。接收到请求后，服务器会启动一个登录线程来处理用户登录操作。

### 请求方法
`POST`

### 请求路径
`/login`

### 请求参数

| 参数名 | 类型   | 是否必需 | 描述               |
|--------|--------|----------|--------------------|
| id     | string | 是       | 用户名或账号       |
| pw     | string | 否       | 密码               |
| type   | string | 否       | 登录类型，默认为 `password` |
| isAuto | bool   | 否       | 是否自动登录，默认为 `False` |

### 响应示例
```json
{
	"msg": "13155555555处理中, 到/check查询处理进度",
	"status": "pass",
	"uid": "7654321xxx"
}
```
```json
{
  "status": "pass",
  "uid": "7654321xxx",
  "msg": "用户名已经在处理了，请稍后再试"
}
```

### /sms 接口

### 描述
处理短信验证码的提交。用于在登录过程中输入并提交短信验证码。

### 请求方法
`POST`

### 请求路径
`/sms`

### 请求参数
| 参数名 | 类型   | 是否必需 | 描述               |
|--------|--------|----------|--------------------|
| uid    | string | 是       | 登录的用户标识符       |
| code     | string | 是     | 短信验证码（必须为6位数字）|
### 响应示例
```json
{
  "status": "pass",
  "msg": "成功提交验证码"
}
```
### 提交成功后 5s后会清除状态 所以在提交成功后 在5s内尽快check 查询cookie
```json
{
  "status": "wrongSMS",
  "msg": "验证码错误"
}
```
### /check 接口

### 描述
检查指定用户的登录状态。用于查询账号的处理进度或结果。

### 请求方法
`POST`

### 请求路径
`/check`

### 请求参数
| 参数名 | 类型   | 是否必需 | 描述               |
|--------|--------|----------|--------------------|
| uid    | string | 是       | 登录的用户标识符       |
### 响应示例
```json
{
  "status": "pass",
  "cookie": "user_cookie",
  "msg": "成功"
}
```
```json
{
  "status": "pending",
  "msg": "正在处理中，请等待"
}
```
```json
{
  "status": "error",
  "msg": "登录失败，请在十秒后重试：错误信息"
}
```
```json
{
  "status": "wrongSMS",
  "msg": "短信验证错误，请重新输入"
}
```
```json
{
  "status": "SMS",
  "msg": "需要短信验证"
}
```
