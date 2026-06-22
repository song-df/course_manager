# 智联学习云课程平台 (CLAUDE.md)

## 项目概述
100门课程、22,647个视频的在线学习平台。三级页面：系列卡片 → 课程列表 → 视频播放。深色主题，响应式设计。

## 架构
```
浏览器 → aiotedu.cc (Nginx) → frps→frpc→WSL server.py(:8080)
认证: aiotedu.cc/api/auth/* → :8001 (FastAPI + SQLite)
```

## 核心文件
| 文件 | 用途 |
|------|------|
| `server.py` | HTTP 服务：API + 视频流 + 静态文件 |
| `index.html` | 首页：10大系列卡片 |
| `series.html` | 系列页：课程卡片 + Wiki资源 |
| `course.html` | 播放页：章节 + 视频（首视频免费） |
| `auth.js` | 鉴权：登录/注册/邀请码 |
| `generate_course_data.py` | 课程数据生成器 |
| `courses_config.json` | 课程目录配置（auto_discover） |
| `series_config.json` | 系列→课程映射 |
| `wiki.html` + `wiki_render.js` | Markdown文档渲染（wiki.js风格） |

## 数据流
`courses_config.json` → `generate_course_data.py` → `course_data.json` → `server.py` → `/api/courses|series`

## 启动命令
```bash
# WSL
cd /mnt/d/workspace/course_resource
python3 server.py --port 8080

# 本地测试
cd D:\workspace\course_resource
python server.py --port 8080
```

## 认证
- JWT Bearer Token, localStorage
- 邀请制注册：50个8位码，API发放
- 固定Token：`7FFc5ANdz0zxm0ulG0dxxrt8OAOHlEw8`

## 运维要点
- 添加新课：视频放入目录 → 编辑 `courses_config.json` → 运行 `generate_course_data.py` → 更新 `series_config.json` → 重启server.py
- 云主机SSH：`ssh -p 22022 -i D:/workspace/ssh_key/js_server_key.pem root@47.100.102.229`
- 认证后端重启：`fuser -k 8001/tcp && cd /www/wwwroot/ai.aiotedu.cc/api && nohup uvicorn main:app --host 127.0.0.1 --port 8001 &`

## 环境运行备忘

### 服务分布（谁在哪里跑）
| 组件 | 主机 | 说明 |
|------|------|------|
| **server.py** | 本地 WSL | 课程API + 视频流，需要访问 E: 盘视频文件 |
| **frpc** | 本地 WSL | 隧道客户端，连云 frps:7000，代理 :8080→:6005 |
| **frps** | 云主机 | 隧道服务端，接收 frpc 连接，暴露 :6005 |
| **Nginx** | 云主机 | 反向代理 aiotedu.cc → :6005 |
| **认证后端** | 云主机 | FastAPI :8001 |

### 启动顺序（本地 WSL）
```bash
# 1. 确认 frpc 在运行（通常已自启）
ps aux | grep frpc | grep -v grep

# 2. 启动 server.py
cd /mnt/d/workspace/course_resource
nohup python3 server.py --port 8080 > /tmp/server_8080.log 2>&1 &

# 3. 健康检查
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/api/courses  # 期望 200
```

### 故障速查
| 症状 | 原因 | 检查命令 |
|------|------|----------|
| 页面空白/无课程 | `/api/courses` 返回 `[]` | `curl -s https://aiotedu.cc/api/courses \| head -c 200` |
| 有课程但视频 404 | WSL server.py 未运行 或 frpc 隧道断裂 | `ps aux \| grep server.py` (WSL) |
| 视频 404 但 API 正常 | `course_data.json` 被清空 | `wc -c /mnt/d/workspace/course_resource/course_data.json` (应为 ~7MB) |

### ⚠️ 禁止事项
- **不要在云主机启动 server.py** — 云主机无 E: 盘，视频全部 404
- **不要在云主机启动 frpc** — 会造成隧道冲突，本地 frpc 无法注册同名代理
- **不要直接编辑云主机的 course_data.json** — 数据源在本地，应从本地上传
