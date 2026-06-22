# MacBook Pro 开发环境接入指南

## 架构说明

```
MacBook (代码编辑)  ←→  ZeroTier  ←→  Windows WSL (服务运行)
                                            ├── server.py :8080
                                            ├── frpc → 云 frps
                                            └── E: 盘视频文件

云主机 (47.100.102.229)
  ├── frps 接收隧道
  ├── Nginx 反向代理
  └── FastAPI 认证后端 :8001
```

**核心原则：Mac 只写代码，服务永远在 Windows WSL 上运行。** 视频存储、course_data.json 生成、frp 隧道都在 Windows 侧，Mac 不需要碰这些。

---

## 1. 基础环境

```bash
# Git（系统自带或 brew install git）
git --version

# Homebrew（可选，装辅助工具用）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## 2. 克隆项目

```bash
git clone https://github.com/song-df/course_manager.git
cd course_manager
```

---

## 3. ZeroTier — 连接 Windows WSL

### 3.1 安装

```bash
# Mac
brew install zerotier-one
sudo zerotier-cli join <网络ID>    # 从 Windows 机的 ZeroTier 网络获取
```

Windows 端同样加入同一 ZeroTier 网络，WSL 内会自动获得 ZeroTier IP。

### 3.2 验证连通

```bash
# 从 Mac ping WSL 的 ZeroTier IP（在 Windows WSL 中用 ip addr 查看 zt 接口）
ping <WSL的ZeroTier IP>

# SSH 到 WSL（如已配置 SSH）
ssh root@<WSL的ZeroTier IP>
```

---

## 4. SSH 免密登录 WSL

### 4.1 生成密钥对

```bash
# Mac 上
ssh-keygen -t ed25519 -C "macbook-dev" -f ~/.ssh/id_ed25519_mac
```

### 4.2 将公钥添加到 WSL

```bash
# 在 Mac 上复制公钥
cat ~/.ssh/id_ed25519_mac.pub

# SSH 到 WSL（先用密码），粘贴到 authorized_keys
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "粘贴的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 4.3 配置 SSH config

`~/.ssh/config`：

```
Host wsl-dev
    HostName <WSL的ZeroTier IP>
    User root
    IdentityFile ~/.ssh/id_ed25519_mac
```

测试：

```bash
ssh wsl-dev "echo 连接成功"
```

---

## 5. 开发工作流

### 方式 A：本地编辑 + Git 同步（推荐）

```bash
# Mac 上编辑代码
# ... 改文件 ...
git add -A && git commit -m "描述改动"
git push

# SSH 到 WSL 拉取更新
ssh wsl-dev "cd /mnt/d/workspace/course_resource && git pull"
```

静态文件（html/js/css/json）无需重启 server.py，下次请求自动生效。

### 方式 B：VS Code Remote-SSH 直接编辑

在 VS Code 中安装 `Remote - SSH` 扩展，添加 `wsl-dev` 主机，直接在 WSL 上编辑文件。**改完即生效**，连 git push/pull 都省了。

```bash
# VS Code 快捷键
Cmd+Shift+P → Remote-SSH: Connect to Host → wsl-dev
# 打开 /mnt/d/workspace/course_resource 目录即可编辑
```

### 方式 C：SFTP 挂载

```bash
# Mac 上安装
brew install sshfs

# 挂载 WSL 项目目录到 Mac 本地
mkdir -p ~/mnt/wsl-project
sshfs wsl-dev:/mnt/d/workspace/course_resource ~/mnt/wsl-project
```

---

## 6. 需要重启服务的情况

| 改动内容 | 需要重启？ |
|----------|-----------|
| HTML / CSS / JS | **不需要**（静态文件每次请求重读） |
| `course_data.json` | **不需要**（API 每次请求重读文件） |
| `server.py` 自身 | **需要** |
| `courses_config.json` / `series_config.json` | **不需要**（仅用于生成 course_data.json） |

重启命令（在 WSL 上执行）：

```bash
ssh wsl-dev "kill \$(pgrep -f 'server.py' | head -1); sleep 1; cd /mnt/d/workspace/course_resource && nohup python3 server.py --port 8080 > /tmp/server_8080.log 2>&1 &"
```

---

## 7. course_data.json 更新（极少发生）

仅在添加新课程时才需要重新生成。**在 Windows 侧操作**：

```bash
# Windows WSL 上
cd /mnt/d/workspace/course_resource
python3 generate_course_data.py

# 然后 git commit & push，Mac 拉取
git add course_data.json && git commit -m "update course data"
git push
```

> Mac 上运行 `generate_course_data.py` 没有意义——它扫描的 E: 盘视频文件只存在于 Windows 上。

---

## 8. 快速命令备忘

```bash
# SSH 到 WSL
ssh wsl-dev

# 查看 WSL 服务状态
ssh wsl-dev "ps aux | grep -E 'server.py|frpc' | grep -v grep"

# 查看 WSL 服务日志
ssh wsl-dev "tail -20 /tmp/server_8080.log"

# 重启 WSL server.py
ssh wsl-dev "kill \$(pgrep -f 'server.py' | head -1); sleep 1; cd /mnt/d/workspace/course_resource && nohup python3 server.py --port 8080 > /tmp/server_8080.log 2>&1 &"

# 验证线上服务
curl -s https://aiotedu.cc/api/courses | python3 -c "import sys,json; print(len(json.load(sys.stdin)),'courses')"
```
