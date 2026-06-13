# Windows 从零安装 Codex

> Codex CLI + Moon Bridge 中转方案 · 国内直连 · 免翻墙免信用卡

---

## 一、安装 nvm 和 Node.js

打开 PowerShell，执行以下命令安装 nvm：

```PowerShell
winget install CoreyButler.NVMforWindows
nvm version
nvm install 24.14.1
nvm list
node -v
```

> ⚠️ 如果 `npm --version` 报权限错误，以**管理员身份**打开 PowerShell 执行：
>
> ```PowerShell
> Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
>
> 输入 **Y** 确认，关掉终端重新打开即可正常使用 npm。

---

## 二、下载并安装 Codex

访问 [OpenAI Codex 快速开始](https://developers.openai.com/codex/quickstart)，下载 Windows 版安装包 `Codex Installer.exe`，双击安装。

> ⚠️ **安装过程中如报错**
>
> 先备份再删除损坏的数据库：
>
> ```PowerShell
> # 备份（以防万一）
> Copy-Item -Path "$env:USERPROFILE\.codex" -Destination "$env:USERPROFILE\.codex.backup" -Recurse
>
> # 删除损坏的数据库
> Remove-Item -Path "$env:USERPROFILE\.codex" -Recurse -Force
> ```
>
> 然后重新运行安装程序。

---

## 三、配置 Moon Bridge（中转）

Moon Bridge 负责将 Codex 的 Anthropic 格式请求转发到 T粒加油站。需要先安装 Go 语言环境。

### 1. 安装 Go

```PowerShell
winget install GoLang.Go
go version

# 查看 Go 环境路径
go env GOROOT    # Go 安装位置，通常 C:\Program Files\Go
go env GOPATH    # 工作目录，默认 C:\Users\<用户名>\go
```

如果想把 GOPATH 改到其他盘（如 D 盘）：

```PowerShell
[System.Environment]::SetEnvironmentVariable('GOPATH', 'D:\go-workspace', 'User')
```

配置国内代理（加速下载）：

```PowerShell
go env -w GOPROXY=https://goproxy.cn,direct
```

### 2. 克隆 Moon Bridge 仓库

用 Git 将 Moon Bridge 下载到本地（如没有 Git，先执行 `winget install Git.Git`）：

```PowerShell
# 创建工作目录（可换成你想要的路径）
mkdir D:\workspace
cd D:\workspace

# 克隆 Moon Bridge
git clone https://github.com/anthropics/moon-bridge.git
cd moon-bridge
```

### 3. 创建配置文件

在 Moon Bridge 目录下创建 `config.yml`，**把 api_key 改成你的 Key**：

```yaml
mode: "Transform"

log:
  level: "info"
  format: "text"

server:
  addr: "127.0.0.1:38440"

persistence:
  active_provider: db_sqlite

extensions:
  deepseek_v4:
    config:
      reinforce_instructions: true
  kimi_workaround:
    config:
      max_tool_rounds: 50
      convergence_margin: 0.8
  db_sqlite:
    enabled: true
    config:
      path: ./data/moonbridge.db
      wal: true
      busy_timeout_ms: 5000
      max_open_conns: 1
  metrics:
    enabled: true
    config:
      default_limit: 100
      max_limit: 1000

cache:
  mode: "explicit"
  ttl: "5m"
  prompt_caching: true
  automatic_prompt_cache: false
  explicit_cache_breakpoints: true
  allow_retention_downgrade: false
  max_breakpoints: 4
  min_cache_tokens: 1024
  expected_reuse: 2
  minimum_value_score: 2048
  min_breakpoint_tokens: 1024

defaults:
  model: "moonbridge"
  max_tokens: 65536

trace:
  enabled: false

providers:
  default:
    base_url = "https://ai.aiotedu.cc"
    api_key = "sk-你的APIKey"
    version: "2023-06-01"
    user_agent: "moonbridge/1.0"
    web_search:
      support: "auto"
    offers:
      - model: deepseek-v4-pro
        pricing:
          input_price: 2
          output_price: 8
          cache_write_price: 1
          cache_read_price: 0.2
      - model: deepseek-v4-flash
        pricing:
          input_price: 1
          output_price: 2
          cache_write_price: 1
          cache_read_price: 0.02
      - model: claude-sonnet-4-6
        pricing:
          input_price: 3
          output_price: 15
          cache_write_price: 3.75
          cache_read_price: 0.30

routes:
  moonbridge:
    model: deepseek-v4-pro
    provider: default
```

### 4. 启动 Moon Bridge

```PowerShell
cd D:\workspace\moon-bridge
go run ./cmd/moonbridge -config config.yml
```

看到 `Moon Bridge 监听于 127.0.0.1:38440` 就说明启动成功。

> **保持此窗口运行**，后续步骤需要 Moon Bridge 在后台持续监听。

---

## 四、配置 Codex 连接 Moon Bridge

新开一个 PowerShell 窗口，逐条执行以下命令来生成 Codex 配置：

### 1. 生成配置

```PowerShell
# 第 1 条：设置 Codex 目录路径
$CODEX_HOME_DIR = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { "$HOME\.codex" }

# 第 2 条：获取默认模型名
$MODEL = go run ./cmd/moonbridge -print-codex-model -config "D:\workspace\moon-bridge\config.yml"

# 第 3 条：生成 config.toml + models_catalog.json
go run ./cmd/moonbridge -print-codex-config "$MODEL" -codex-base-url "http://127.0.0.1:38440/v1" -codex-home "$CODEX_HOME_DIR" -config "D:\workspace\moon-bridge\config.yml" | Set-Content -Path "$CODEX_HOME_DIR\config.toml" -NoNewline
```

> 注意：上述路径 `D:\workspace\moon-bridge` 请替换为你的实际 Moon Bridge 目录。

### 2. 额外配置（手动添加到 config.toml）

编辑 `~/.codex/config.toml`，确保包含以下内容：

```toml
model = "moonbridge"
model_provider = "moonbridge"
model_context_window = 1000000
model_max_output_tokens = 384000
model_catalog_json = "C:\\Users\\<用户名>\\.codex\\models_catalog.json"

[model_providers.moonbridge]
name = "Moon Bridge"
base_url = "http://127.0.0.1:38440/v1"
wire_api = "responses"
```

路径中的 `<用户名>` 请替换为你的 Windows 用户名。

### 3. 重启 Codex App

完成配置后，完全退出 Codex App（右键任务栏图标退出或任务管理器结束进程），然后重新启动。

---

## 五、验证是否成功

重启 Codex 后，在 Codex 终端中测试对话。如果正常回复，说明配置成功。

> ✅ **成功的标志：**
> - Moon Bridge 窗口中看到请求日志
> - Codex 能正常回复对话
> - [T粒加油站](https://ai.aiotedu.cc/) 的使用记录中能看到扣费

---

## 常见问题

### Q: Codex 提示 "No available channel for model claude-sonnet-4-20250514"？

这是模型名不匹配。当前 T粒加油站使用的 Claude Sonnet 模型 ID 是 `claude-sonnet-4-6`，不是 `claude-sonnet-4-20250514`。请按上文配置文件使用正确的模型名。

### Q: npm install 报权限错误？

需要以**管理员身份**打开 PowerShell，执行 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`，输入 Y 确认后重启终端。

### Q: go run 下载依赖很慢？

已在上文配置了 `GOPROXY=https://goproxy.cn,direct`，国内下载应该在秒级完成。如果没有执行此命令，请先执行。

### Q: 如何确认配置的是哪个模型？

Codex 最终使用的模型由 Moon Bridge 的 `routes.moonbridge.model` 决定（配置文件中设为 `deepseek-v4-pro`）。如果要换模型，修改该行并重启 Moon Bridge 即可。

---

还没有 Key？[立即注册](https://ai.aiotedu.cc/register)
