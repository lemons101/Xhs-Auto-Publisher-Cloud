# 第12节 实验手册：云端部署小红书自动发布 Skill

> 配套课程：AI 业务流架构师 · 第12节 云端执行体与跨端登录协作
> 前置条件：已准备好 `lemons101/Xhs-Auto-Publisher-Cloud` 仓库，并能让龙虾访问目标云服务器
> 操作方式：全程把任务发送给龙虾执行，学员无需直接登录服务器
> 预计耗时：实验一 ~30 分钟，实验二 ~20 分钟

---

## 实验目标

1. 理解小红书自动发布 Skill 的云端最小可运行链路：生成登录二维码截图、生成 payload、交给龙虾转发到飞书群。
2. 掌握一个 Agent Skill 项目在 Ubuntu 服务器上的标准部署流程：拉取仓库、安装系统依赖、初始化 `.venv`、安装 Playwright Chromium。
3. 用 `MODE=draft` 完成安全验证，只跑到二维码登录阶段，不触发真实内容发布。
4. 验证云端运行产物是否完整生成：`login_qr.png` 和 `login_qr.payload.json`。
5. 明确本节边界：先跑通手动验证，不配置 nginx、不配置 systemd、不做公网二维码访问。

---

## 实验一：部署云端 Skill 项目

### 架构说明

```text
GitHub 仓库
  -> 云服务器 /root/projects/xhs-auto-publisher-cloud
  -> install_system_ubuntu.sh 安装系统依赖
  -> bootstrap_project.sh 创建 .venv 并安装 Playwright
  -> .env 设置 MODE=draft
  -> run_with_xvfb.sh 在虚拟显示环境中启动浏览器
```

这一节的重点不是让服务器真正发布小红书笔记，而是先确认云端执行环境能把浏览器跑起来。

### 1a. 让龙虾确认任务边界

在飞书中发送：

```text
@檬爪一号🦞 你现在帮我部署一个 Skill 到云服务器。

目标仓库：
GitHub - lemons101/Xhs-Auto-Publisher-Cloud
https://github.com/lemons101/Xhs-Auto-Publisher-Cloud

目标机器信息：
- Ubuntu 24.04.4 LTS
- root 用户
- 项目部署目录：/root/projects/xhs-auto-publisher-cloud

这次只做“可运行性验证”，不要真的发布内容。

重要边界：
1. 不要配置 nginx。
2. 不要配置 systemd。
3. 不要配置 XHS_PUBLIC_RUNTIME_BASE_URL。
4. 不要删除仓库里的文档和示例文件。
5. 不要修改核心逻辑，除非遇到明确报错并且必须修复。
6. 不要绕过扫码、滑块、验证码或平台风控。
7. .env 里的 MODE 必须设置为 draft。
8. 如果测试跑到需要扫码登录，生成二维码截图和 payload 后就停下来，等待我下一步处理。

你执行时请严格按步骤来，每完成一步就回报：
1. 执行了什么命令
2. 成功还是失败
3. 关键输出是什么
4. 如果失败，贴核心报错
5. 当前卡在哪一步
```

**确认要点**：龙虾明确知道本次不是正式发布任务，而是云端可运行性验证。

### 1b. 拉取仓库到部署目录

继续发送：

```text
请先拉取仓库到指定部署目录。

执行命令：

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

执行后请回报：
1. 当前目录
2. git status 输出
3. 是否已经成功部署到 /root/projects/xhs-auto-publisher-cloud
```

**确认要点**：`pwd` 输出应为 `/root/projects/xhs-auto-publisher-cloud`。

### 1c. 安装系统依赖

在飞书中发送：

```text
请执行项目自带的系统依赖安装脚本：

bash /root/projects/xhs-auto-publisher-cloud/deploy/install_system_ubuntu.sh

执行完成后请回报：
1. 命令是否成功退出
2. 是否出现 apt / package / permission 相关错误
3. 关键输出摘要
```

> 🔍 **观察要点**：这一步主要解决 Playwright Chromium 在 Ubuntu 上运行所需的系统库和 Xvfb 环境。

### 1d. 初始化项目和 Python 环境

在飞书中发送：

```text
请执行项目初始化脚本：

cd /root/projects/xhs-auto-publisher-cloud && bash deploy/bootstrap_project.sh

然后执行以下检查命令：

cd /root/projects/xhs-auto-publisher-cloud
test -d .venv && echo ".venv ok"
.venv/bin/python --version
.venv/bin/python -c "import playwright; print('playwright ok')"
.venv/bin/python -m playwright --version

执行完成后请回报：
1. .venv 是否创建成功
2. Python 版本
3. Playwright 是否可 import
4. Playwright Chromium 安装是否成功
5. 如失败，请贴核心报错
```

**确认要点**：必须看到 `.venv ok` 和 `playwright ok`。

### 1e. 复制 `.env` 并设置 draft 模式

在飞书中发送：

```text
请复制环境变量模板，并把 MODE 设置为 draft。

执行命令：

cd /root/projects/xhs-auto-publisher-cloud
cp deploy/env.example .env

if grep -q '^MODE=' .env; then
  sed -i 's/^MODE=.*/MODE=draft/' .env
else
  printf '\nMODE=draft\n' >> .env
fi

grep '^MODE=' .env

执行后请回报 grep 输出。
```

期望输出：

```text
MODE=draft
```

> ✅ `MODE=draft` 是本实验的安全边界：即使流程继续向后走，也不应该执行真实发布。

---

## 实验二：运行云端测试并验证二维码链路

### 架构说明

```text
run_with_xvfb.sh
  -> 启动 Xvfb 虚拟显示
  -> 启动 Playwright Chromium
  -> 打开小红书创作者平台
  -> 触发扫码登录
  -> 保存 runtime/runs/<run_id>/screenshots/login_qr.png
  -> 保存 runtime/lobster-notify/<run_id>/login_qr.payload.json
```

这一节只验证“二维码截图 + payload”链路。后续由龙虾把 payload 中的信息转发到飞书群，不需要在本实验中配置公网访问。

### 2a. 执行手动测试

在飞书中发送：

```text
请执行一次手动测试：

cd /root/projects/xhs-auto-publisher-cloud && bash deploy/run_with_xvfb.sh

注意：
1. 这次只做可运行性验证，不要真的发布内容。
2. 如果程序跑到小红书扫码登录阶段，不要继续配置 nginx，不要配置 systemd。
3. 只要生成二维码截图和 payload，就停下来回报路径。
4. 如果脚本异常退出，请贴核心报错。
```

> 🔍 **观察要点**：如果看到登录二维码相关输出，不代表失败，恰恰说明云端浏览器已经跑起来了。

### 2b. 检查运行产物

在飞书中发送：

```text
请检查本次运行是否生成二维码截图和 lobster notify payload。

执行命令：

cd /root/projects/xhs-auto-publisher-cloud

RUN_ID="$(find runtime/runs -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort | tail -n 1)"
echo "run_id=$RUN_ID"

QR_PATH="/root/projects/xhs-auto-publisher-cloud/runtime/runs/$RUN_ID/screenshots/login_qr.png"
PAYLOAD_PATH="/root/projects/xhs-auto-publisher-cloud/runtime/lobster-notify/$RUN_ID/login_qr.payload.json"

echo "二维码图片路径：$QR_PATH"
echo "payload 文件路径：$PAYLOAD_PATH"

test -f "$QR_PATH" && echo "login_qr.png ok" || echo "login_qr.png missing"
test -f "$PAYLOAD_PATH" && echo "login_qr.payload.json ok" || echo "login_qr.payload.json missing"

if [ -f "$PAYLOAD_PATH" ]; then
  echo "payload preview:"
  cat "$PAYLOAD_PATH"
fi

请把 run_id、二维码图片路径、payload 文件路径回报给我。
```

**确认要点**：

- 输出 `login_qr.png ok`
- 输出 `login_qr.payload.json ok`
- `run_id` 非空

### 2c. 成功后的回报格式

如果 2b 检查通过，让龙虾按下面格式回报：

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

### 2d. 失败后的回报格式

如果任意一步失败，让龙虾按下面格式回报：

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

---

## 验收标准

完成本实验时，应满足以下条件：

- 项目目录已正确部署到 `/root/projects/xhs-auto-publisher-cloud`
- `.venv` 创建成功
- Playwright Chromium 安装成功
- `deploy/run_with_xvfb.sh` 能成功跑起测试
- 成功生成 `runtime/runs/<run_id>/screenshots/login_qr.png`
- 成功生成 `runtime/lobster-notify/<run_id>/login_qr.payload.json`
- 测试停在扫码登录阶段，等待人工下一步处理

---

## 实验记录

请记录你在实验过程中遇到的任何与预期不符的情况：

| # | 发生在哪一步 | 预期行为 | 实际行为 | 你的解决方法 |
|---|------------|----------|---------|------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## 常见问题排查

- `git clone` 失败：检查服务器是否能访问 GitHub，或改用 SSH/代理方式拉取。
- `install_system_ubuntu.sh` 失败：检查当前用户是否为 root，检查 apt 源是否可用。
- `.venv` 没有生成：查看 `bootstrap_project.sh` 中 Python 版本和 venv 创建日志。
- Playwright Chromium 安装失败：重新执行 `bash deploy/bootstrap_project.sh`，并确认系统依赖脚本已经跑完。
- `run_with_xvfb.sh` 启动失败：检查 Xvfb 是否安装，查看脚本输出中的 DISPLAY 和 Chromium 报错。
- 没有生成 `login_qr.png`：查看最近一次 `runtime/runs/<run_id>/actions.jsonl` 和 `screenshots/` 目录。
- 没有生成 `login_qr.payload.json`：检查 `runtime/lobster-notify/` 目录，以及项目中的 lobster notify 生成逻辑是否被触发。
- 误进入真实发布流程：立即停止任务，确认 `.env` 中 `MODE=draft`。

> 欢迎把你的实验记录和踩坑发现分享到课程社群。
