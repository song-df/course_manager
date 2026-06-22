# MacBook Pro 开发环境接入指南

## 前置条件

- macOS 14+ (Sonoma/Sequoia)
- Homebrew（[brew.sh](https://brew.sh)）
- Git
- 与 Windows 开发机在同一局域网（如需共享视频文件）

---

## 1. 克隆项目

```bash
git clone https://github.com/song-df/course_manager.git
cd course_manager
```

或从 Windows 机直接复制（含完整 git 历史）：

```bash
cd /path/to/workspace
git clone D:\\workspace\\course_resource course_resource   # 如果已挂载 Windows 共享
```

---

## 2. Python 环境

```bash
# macOS 自带 Python 3，确认版本 >= 3.9
python3 --version

# 本项目无外部依赖，仅用标准库，无需 pip install
```

---

## 3. 适配 server.py 路径（关键）

`server.py` 当前只适配了 Windows 和 WSL，需要添加 macOS 支持。

### 3.1 修改路径常量

编辑 `server.py` 顶部，在 `IN_WSL` 检测后新增：

```python
# Detect platform
IN_WSL = 'WSL_DISTRO_NAME' in os.environ or os.path.exists('/proc/sys/fs/binfmt_misc/WSLInterop')
IN_MAC = sys.platform == 'darwin'

if IN_WSL:
    COURSE_DATA = '/mnt/d/workspace/course_resource/course_data.json'
    SERIES_CONFIG = '/mnt/d/workspace/course_resource/series_config.json'
    ROOT = '/mnt/d/workspace/course_resource'
elif IN_MAC:
    # 修改为你的实际路径
    COURSE_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'course_data.json')
    SERIES_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'series_config.json')
    ROOT = os.path.dirname(os.path.abspath(__file__))
else:
    COURSE_DATA = r'D:\workspace\course_resource\course_data.json'
    SERIES_CONFIG = r'D:\workspace\course_resource\series_config.json'
    ROOT = 'D:\\workspace\\course_resource'
```

### 3.2 修改路径标准化函数

`normalize_path` 函数需要处理 macOS 视频文件路径：

```python
def normalize_path(raw_path):
    """Convert any path format to the platform-native absolute path."""
    path = raw_path.replace('\\', '/')

    if IN_WSL:
        path = re.sub(r'^([A-Za-z]):/', lambda m: f'/mnt/{m.group(1).lower()}/', path)
    elif IN_MAC:
        # macOS: 如果是 Windows 路径 (E:/xxx)，需要映射到实际视频目录
        # 方式A: 挂载了 Windows 共享 → 映射到 /Volumes/xxx
        # 方式B: 本地有视频副本 → 映射到本地路径
        # 方式C: 远程代理 → 保持原样，视频由 Windows 机提供
        pass  # 详见下方「视频文件」章节
    else:
        path = path.replace('/', '\\')
    return path
```

> **建议：** 将路径配置提取为环境变量，避免每次切换平台都改代码。见附录 A。

---

## 4. SSH 密钥配置

从 Windows 机复制 SSH 密钥到 Mac，用于连接云主机。

```bash
# 在 Mac 上
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 方式A: 从 Windows 机 scp 获取
# （Windows 需先开启 SSH 服务 或 用 U盘/网盘 中转）
scp 用户名@Windows机IP:D:/workspace/ssh_key/js_server_key.pem ~/.ssh/
chmod 600 ~/.ssh/js_server_key.pem

# 方式B: 手动复制内容
# 在 Windows 上: type D:\workspace\ssh_key\js_server_key.pem
# 在 Mac 上: nano ~/.ssh/js_server_key.pem （粘贴内容）
# chmod 600 ~/.ssh/js_server_key.pem
```

测试连接：

```bash
ssh -p 22022 -i ~/.ssh/js_server_key.pem root@47.100.102.229 "echo OK"
```

---

## 5. FRP 隧道客户端

### 5.1 安装 frpc

```bash
# 下载最新 frp（替换版本号为最新）
cd /tmp
curl -LO https://github.com/fatedier/frp/releases/download/v0.61.2/frp_0.61.2_darwin_amd64.tar.gz
tar xzf frp_0.61.2_darwin_amd64.tar.gz
sudo cp frp_0.61.2_darwin_amd64/frpc /usr/local/bin/
sudo chmod +x /usr/local/bin/frpc
```

### 5.2 配置 frpc

```bash
mkdir -p ~/.frp
```

创建 `~/.frp/frpc.toml`（内容与 Windows `d:\workspace\course_resource\frpc.toml` 一致）：

```toml
serverAddr = "47.100.102.229"
serverPort = 7000

auth.method = "token"
auth.token = "<从 Windows 机 frpc.toml 复制>"

[[proxies]]
name = "aiotedu_courses"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8080
remotePort = 6005
```

> ⚠️ **注意：** 同一时间只能有一台机器运行 frpc 连接云 frps，否则隧道名称冲突。在 Mac 开发时，需先停掉 Windows WSL 的 frpc。

### 5.3 启动 frpc

```bash
# 前台测试
frpc -c ~/.frp/frpc.toml

# 确认正常后，后台运行
nohup frpc -c ~/.frp/frpc.toml > /tmp/frpc.log 2>&1 &
```

---

## 6. 视频文件（三种方案）

### 方案 A：SMB 挂载 Windows 视频盘（推荐局域网开发）

在 Windows 上共享 E: 盘，Mac 挂载后直接访问：

```bash
# Mac 上挂载 Windows 共享
open smb://Windows机IP/kkb-course    # E:\kkb-course
open smb://Windows机IP/AI_Agent_学习  # E:\AI_Agent_学习

# 挂载后在 /Volumes/ 下可见
ls /Volumes/kkb-course
```

然后修改 `normalize_path` 映射 Windows 路径到挂载点，或重新生成 `course_data.json`（见下方）。

### 方案 B：本地视频副本（独立开发）

将常用课程视频拷贝到 Mac 本地：

```bash
# 在 Mac 上
mkdir -p ~/videos/kkb-course
# 从 Windows 复制需要的课程
rsync -avP 用户名@Windows机IP:/e/kkb-course/某课程/ ~/videos/kkb-course/某课程/
```

然后修改 `courses_config.json` 的 `base_dir` 指向 `~/videos/kkb-course`，重新生成 `course_data.json`。

### 方案 C：仅前端开发（最简单）

不改动视频和 server.py，只编辑 HTML/JS/CSS：

```bash
# 本地启动仅用于预览静态页面的轻量服务器
python3 -m http.server 8080
# 打开 http://localhost:8080/course.html?id=agent-guide-videos

# 视频部分通过修改 API base URL 指向线上来调试
# 或直接用浏览器访问 https://aiotedu.cc 看效果
```

---

## 7. 重新生成 course_data.json（方案 A/B 需要）

```bash
cd /path/to/course_resource

# 1. 确认 courses_config.json 中 base_dir 指向正确的视频目录
# 方案A: base_dir 指向 /Volumes/xxx
# 方案B: base_dir 指向 ~/videos/kkb-course

# 2. 运行生成器（会自动备份旧文件）
python3 generate_course_data.py

# 3. 验证
python3 -c "import json; d=json.load(open('course_data.json')); print(f'{len(d)} courses')"
```

---

## 8. 启动开发服务

```bash
# 1. 启动 server.py
cd /path/to/course_resource
python3 server.py --port 8080

# 2. 另开终端，启动 frpc
frpc -c ~/.frp/frpc.toml

# 3. 本地测试
curl http://localhost:8080/api/courses | python3 -m json.tool | head -20
```

---

## 9. 日常开发工作流

```bash
# 拉取最新代码
git pull

# 开发 & 测试
# ... 编辑代码 ...

# server.py 会自动重载静态文件（每次都重新读取）
# 如果修改了 server.py 本身，需重启：
kill $(pgrep -f "server.py")
python3 server.py --port 8080 &

# 提交
git add -A && git commit -m "描述改动"
git push

# 回到 Windows 机后：
# 1. git pull 拉取 Mac 上的提交
# 2. 停掉 Mac frpc → 启动 WSL frpc（恢复 Windows 为隧道端点）
```

---

## 10. 两台机器切换清单

| 步骤 | Mac → Windows | Windows → Mac |
|------|---------------|---------------|
| 1 | Mac: `killall frpc` | Windows: `wsl kill $(pgrep frpc)` |
| 2 | Mac: `killall python3` (server.py) | Windows: WSL 停 server.py |
| 3 | Windows: 启动 WSL server.py | Mac: 启动 server.py |
| 4 | Windows: 启动 WSL frpc | Mac: 启动 frpc |
| 5 | 浏览器访问验证 | 浏览器访问验证 |

---

## 附录 A：环境变量优化（可选）

将路径配置提取为环境变量，避免修改代码：

```python
# server.py 顶部改为：
COURSE_DATA = os.environ.get('CR_COURSE_DATA',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'course_data.json'))
SERIES_CONFIG = os.environ.get('CR_SERIES_CONFIG',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'series_config.json'))
ROOT = os.environ.get('CR_ROOT',
    os.path.dirname(os.path.abspath(__file__)))
```

启动时：

```bash
# Mac
CR_COURSE_DATA=/Users/me/course_resource/course_data.json \
CR_SERIES_CONFIG=/Users/me/course_resource/series_config.json \
CR_ROOT=/Users/me/course_resource \
python3 server.py --port 8080

# 或写入 ~/.zshrc
export CR_COURSE_DATA=/Users/me/course_resource/course_data.json
```

---

## 附录 B：Git 用户配置

```bash
git config --global user.name "song-df"
git config --global user.email "你的邮箱"

# 配置 GitHub 认证（推荐 gh CLI）
brew install gh
gh auth login
```
