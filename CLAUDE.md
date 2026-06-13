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
