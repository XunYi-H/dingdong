function resetState() {
    uid = "";
    isLoginFlag = false;
    isSmsFlag = false;
    clearCountdown();
    enableSubmitButton();
    document.getElementById("input1").value = "";
    document.getElementById("input2").value = "";
    document.getElementById("remarks").value = "";
    document.getElementById("uid-display").textContent = "";
    document.getElementById("status-display").textContent = "";
}
console.log(`Author:'smallfawn'`)
let waitTime = 60;
let uid = "";
let countdownInterval = null;
let isLoginFlag = false; // 新增标志位
let isSmsFlag = false;
async function sub() {
    const input1 = document.getElementById("input1").value;
    const input2 = document.getElementById("input2").value;
    const submitButton = document.getElementById("submit-button");
    const remarks = document.getElementById("remarks").value || "GoDongGoCar"; // Get the remark input value
    if (input1 && input2) {
        await loginApi(input1, input2, remarks);
        if (uid) {
            startCountdown(waitTime);
            submitButton.disabled = true;
            //防止死锁
            document.getElementById("uid-display").textContent = `${uid}`;
            await new Promise((resolve) => setTimeout(resolve, 2 * 1000));
            for (let i = 0; i < waitTime; i++) {
                await new Promise((resolve) => setTimeout(resolve, 2 * 1000));
                if (!isLoginFlag && !isSmsFlag) {
                    await check(uid);
                } else {
                    break;
                }
            }
            // 登录完成或发生错误后重置标志位，使用户可以再次提交
            if (isLoginFlag || isSmsFlag) {
                isLoginFlag = false;
                isSmsFlag = false;
                clearCountdown();  // 清除倒计时
                enableSubmitButton();  // 允许再次提交
            }
        }
        resetState()
    } else {
        alert("请输入账号和密码");
    }
}

function startCountdown(seconds) {
    const countdownTimer = document.getElementById("countdown-timer");
    countdownTimer.textContent = `(${seconds}s)`;
    countdownInterval = setInterval(() => {
        seconds--;
        countdownTimer.textContent = `(${seconds}s)`;
        if (seconds <= 0) {
            clearInterval(countdownInterval);
            countdownTimer.textContent = "";
            document.getElementById("submit-button").disabled = false;
        }
    }, 1000);
}
function clearCountdown() {
    clearInterval(countdownInterval);
    const countdownTimer = document.getElementById("countdown-timer");
    countdownTimer.textContent = "";
    document.getElementById("submit-button").disabled = false;
}
async function loginApi(id, pw, remarks) {
    id = id + "";
    pw = pw + "";

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                id,
                pw,
                remarks
            }),
        });
        if (response.ok) {
            const result = await response.json();
            if (result.status === "pass") {
                uid = result.uid;
                document.getElementById("uid-display").textContent = `${result.msg}`;
                alert("提交成功");
            } else {
                alert(result.message);
            }
        } else {
            console.error("Error:", response);
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

async function check(uid) {
    uid = uid + "";

    try {
        const response = await fetch("/check", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                uid
            }),
        });
        if (response.ok) {
            const result = await response.json();
            document.getElementById("uid-display").textContent = `${result.msg}`;
            if (result.status === "pass") {
                isLoginFlag = true;
                alert("登录成功");
                enableSubmitButton();
                clearCountdown();
                resetState()
                return; // 退出函数
            }
            if (result.status === "pending") {
            }
            if (result.status === "error") {
                if (result.msg.indexOf("未找到") > -1) {
                    //提示重新登录

                }
                isLoginFlag = true;
                alert("登录失败" + result.msg);
                enableSubmitButton();
                clearCountdown();
                resetState()
                return
            }
            if (result.status === "wrongSMS") {
                isLoginFlag = true;
                enableSubmitButton();
                clearCountdown();
                alert("验证码错误");
                resetState()
                return

            }
            if (result.status === "SMS") {
                isSmsFlag = true;
                openDialog();
                return
            }
        } else {
            console.error("Error:", response);
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

async function submitSmsCode() {
    const code = document.getElementById("sms-code").value;
    if (uid) {
        if (code) {
            await smsApi(uid, code);
            isSmsFlag = false; // 验证码验证完成后设置为false
            for (let i = 0; i < waitTime; i++) {
                await new Promise((resolve) => setTimeout(resolve, 2 * 1000));
                if (!isSmsFlag) {
                    await check(uid);
                    break; // 退出循环
                }
            }
            closeDialog();
        } else {
            alert("请输入验证码");
        }
    }
}
//检测青龙
async function checkStatus() {
    try {
        const response = await fetch("/status", {
            method: "GET",
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("status-box").textContent = result.msg;
            document.getElementById("name").textContent = result.data.name;
        } else {
            document.getElementById("status-box").textContent = "Error fetching status.";
        }
    } catch (error) {
        document.getElementById("status-box").textContent = "Error: " + error.message;
    }
}

document.addEventListener("DOMContentLoaded", checkStatus);




async function smsApi(uid, code) {
    uid = uid + "";
    code = code + "";
    try {
        const response = await fetch("/sms", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                uid,
                code,
            }),
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("uid-display").textContent = `${result.msg}`;
            if (result.status === "pass") {
                alert("提交验证码成功");
                clearCountdown();
            } else if (result.status === "wrongSMS") {
                alert("验证码错误");
            } else if (result.status === "error") {
                alert("提交验证码失败" + result.msg);
                isSmsFlag = true;
            }
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

function openDialog() {
    const dialog = document.getElementById("sms-dialog");
    dialog.showModal();
}

function closeDialog() {
    const dialog = document.getElementById("sms-dialog");
    dialog.close();
}
function enableSubmitButton() {
    const submitButton = document.getElementById("submit-button");
    submitButton.disabled = false;
}