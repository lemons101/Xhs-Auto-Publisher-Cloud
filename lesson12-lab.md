# 第 12 节实验手册：云端部署小红书自动发布 Skill

## 实验目标

1. 理解小红书自动发布 Skill 的云端最小可运行链路：生成登录二维码截图 -> 生成 payload -> 交给龙虾转发到飞书群。
2. 掌握在 Ubuntu 服务器上部署 Agent 工具项目的基本流程：拉取仓库、安装系统依赖、初始化 `.venv`、安装 Playwright Chromium。
3. 用 `MODE=draft` 完成安全验证，跑通登录二维码生成流程，但不触发真实内容发布。
4. 验证运行产物是否完整生成：`login_qr.png` 和 `login_qr.payload.json`。
5. 明确本实验的边界：先跑通手动验证，不配置 nginx、不配置 systemd、不做公网二维码访问。

## 实验背景

这一节我们要把本地的小红书自动发布能力放到云服务器上运行。

但这次不是为了直接发布笔记，而是为了验证一条更基础、更安全的云端协作链路：

```text
云服务器启动 Skill
-> 小红书创作者平台要求扫码登录
-> Skill 生成二维码截图
-> Skill 生成 lobster notify payload
-> 后续由龙虾把二维码图片发到飞书群
-> 人工扫码继续后续流程
```

所以，本实验的成功标准不是“发布成功”，而是：

- 云端项目能跑起来
- 虚拟浏览器能启动
- 小红书登录二维码能截图
- 通知 payload 能生成

只要二维码和 payload 都出现，就说明这一节的部署验证已经完成。

## 直接复制给龙虾的任务卡

下面这一整段可以直接复制粘贴给龙虾执行。

```text
@檬爪一号🦞 你现在帮我部署一个 Skill 到云服务器。

目标仓库：
GitHub - lemons101/Xhs-Auto-Publisher-Cloud
https://github.com/lemons101/Xhs-Auto-Publisher-Cloud

目标机器信息：
- Ubuntu 24.04.4 LTS
- root 用户
- 项目部署目录：/root/projects/xhs-auto-publisher-cloud

部署要求：
1. 从 GitHub 拉取仓库到 `/root/projects/xhs-auto-publisher-cloud`
2. 执行项目自带的系统依赖安装脚本：
   `bash /root/projects/xhs-auto-publisher-cloud/deploy/install_system_ubuntu.sh`
3. 执行项目自带的初始化脚本：
   `cd /root/projects/xhs-auto-publisher-cloud && bash deploy/bootstrap_project.sh`
4. 复制环境变量模板：
   `cd /root/projects/xhs-auto-publisher-cloud && cp deploy/env.example .env`
5. 这次先不要改复杂配置，不需要 nginx，不需要 `XHS_PUBLIC_RUNTIME_BASE_URL`
6. 这次只做“可运行性验证”，不要真的发布内容；把 `.env` 里的 `MODE` 设为 `draft`
7. 执行一次手动测试：
   `cd /root/projects/xhs-auto-publisher-cloud && bash deploy/run_with_xvfb.sh`
8. 运行后检查以下文件是否生成：
   - `runtime/runs/<run_id>/screenshots/login_qr.png`
   - `runtime/lobster-notify/<run_id>/login_qr.payload.json`
9. 如果已经生成二维码截图和 payload，就说明部署成功
10. 暂时先不要配置 systemd，先把手动验证跑通再说

重要说明：
- 这个项目当前只走一条链路：生成二维码截图 -> 生成 payload -> 后续由龙虾把图片发到飞书群
- 不要再额外配置公网二维码访问
- 不要引入 nginx 方案
- 不要删除仓库里的文档和示例文件
- 不要修改核心逻辑，除非遇到明确报错并且必须修复
- 不要绕过扫码、滑块、验证码或平台风控

你执行时请严格按步骤来，每完成一步就回报：
1. 执行了什么命令
2. 成功还是失败
3. 关键输出是什么
4. 如果失败，贴核心报错
5. 当前卡在哪一步

验收标准：
- 项目目录已正确部署到 `/root/projects/xhs-auto-publisher-cloud`
- `.venv` 创建成功
- Playwright Chromium 安装成功
- 能成功跑起测试
- 成功生成 `login_qr.png`
- 成功生成 `login_qr.payload.json`

如果测试跑到需要扫码登录这一步，就停下来，把：
- run_id
- 二维码图片路径
- payload 文件路径
回给我，等待我下一步处理。
```

## 执行命令清单

如果龙虾需要明确命令，就按下面这些命令逐步执行，并在每一步后回报执行结果。

### 1. 拉取仓库

```bash
mkdir -p /root/projects

if [ -d /root/projects/xhs-auto-publisher-cloud/.git ]; then
  cd /root/projects/xhs-auto-publisher-cloud
  git pull --ff-only
else
  git clone https://github.com/lemons101/Xhs-Auto-Publisher-Cloud.git /root/projects/xhs-auto-publisher-cloud
fi

cd /root/projects/xhs-auto-publisher-cloud
pwd
git status --short
```

### 2. 安装系统依赖

```bash
bash /root/projects/xhs-auto-publisher-cloud/deploy/install_system_ubuntu.sh
```

### 3. 初始化项目

```bash
cd /root/projects/xhs-auto-publisher-cloud
bash deploy/bootstrap_project.sh
```

检查初始化结果：

```bash
cd /root/projects/xhs-auto-publisher-cloud
test -d .venv && echo ".venv ok"
.venv/bin/python -c "import playwright; print('playwright ok')"
.venv/bin/python -m playwright --version
```

### 4. 复制环境变量模板

```bash
cd /root/projects/xhs-auto-publisher-cloud
cp deploy/env.example .env
```

### 5. 设置 `MODE=draft`

```bash
cd /root/projects/xhs-auto-publisher-cloud

if grep -q '^MODE=' .env; then
  sed -i 's/^MODE=.*/MODE=draft/' .env
else
  printf '\nMODE=draft\n' >> .env
fi

grep '^MODE=' .env
```

期望输出：

```text
MODE=draft
```

### 6. 执行手动测试

```bash
cd /root/projects/xhs-auto-publisher-cloud
bash deploy/run_with_xvfb.sh
```

注意：这一步如果跑到扫码登录阶段，不要继续扫码，不要配置 systemd，也不要发布内容。只检查二维码截图和 payload 是否生成。

### 7. 检查二维码截图和 payload

```bash
cd /root/projects/xhs-auto-publisher-cloud

RUN_ID="$(find runtime/runs -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort | tail -n 1)"
echo "run_id=$RUN_ID"

QR_PATH="/root/projects/xhs-auto-publisher-cloud/runtime/runs/$RUN_ID/screenshots/login_qr.png"
PAYLOAD_PATH="/root/projects/xhs-auto-publisher-cloud/runtime/lobster-notify/$RUN_ID/login_qr.payload.json"

echo "二维码图片路径：$QR_PATH"
echo "payload 文件路径：$PAYLOAD_PATH"

test -f "$QR_PATH" && echo "login_qr.png ok" || echo "login_qr.png missing"
test -f "$PAYLOAD_PATH" && echo "login_qr.payload.json ok" || echo "login_qr.payload.json missing"
```

## 成功后回报模板

```text
部署验证已跑到二维码阶段。

run_id:
<run_id>

二维码图片路径:
/root/projects/xhs-auto-publisher-cloud/runtime/runs/<run_id>/screenshots/login_qr.png

payload 文件路径:
/root/projects/xhs-auto-publisher-cloud/runtime/lobster-notify/<run_id>/login_qr.payload.json

当前状态:
等待人工下一步处理。
```

## 失败时回报模板

```text
失败步骤:
<步骤编号和名称>

执行命令:
<刚执行的命令>

核心报错:
<关键报错>

当前卡点:
<一句话说明卡在哪里>
```

## 本实验不要做的事

- 不要配置 nginx。
- 不要配置 systemd。
- 不要配置 `XHS_PUBLIC_RUNTIME_BASE_URL`。
- 不要真实发布小红书内容。
- 不要删除仓库文档和示例文件。
- 不要为了绕过扫码、滑块、验证码或平台风控而修改逻辑。
