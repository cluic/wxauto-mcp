# wxauto MCP Server

微信自动化 MCP (Model Context Protocol) 服务器，为 AI 开发工具提供微信自动化能力。

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-1.0+-orange.svg)](https://modelcontextprotocol.io/)

## 功能特性

- **MCP 协议支持**: 完整支持 Model Context Protocol
- **消息操作**: 发送文本、图片、文件、链接卡片消息
- **联系人管理**: 获取好友列表、切换聊天、获取聊天信息
- **会话管理**: 获取会话列表、筛选未读消息
- **文件传输**: 发送单个或批量文件
- **好友管理**: 获取新好友请求、接受好友、添加新好友
- **多种传输**: 支持 stdio、HTTP/SSE 传输方式
- **AI 工具集成**: 支持 Claude Code、Cursor 等开发工具
- **一键安装**: 自动配置到 AI 应用，无需手动编辑配置文件
- **全局单例**: 自动检测并复用已运行的服务器实例，避免资源浪费和冲突

## 系统要求

- Windows 11/10
- Python 3.11+
- 微信已登录
- wxautox4 激活

## PyPI 自动发布

本项目已配置 PyPI Publishing，推送版本标签即可自动发布：

```bash
# 发布新版本
git tag v1.0.1
git push origin v1.0.1
```

GitHub Actions 会自动构建并创建 Release，PyPI 会自动发布新版本。

## 快速安装

```bash
pip install wxauto-mcp
```

## 使用

### 一键自动安装（推荐）

```bash
wxauto-mcp --install
```

这将自动配置 MCP Server 到 **Claude Desktop** 和 **Claude Code**，无需手动编辑配置文件。

### 生成配置文件

```bash
# 生成配置文件到默认目录 (./mcp-configs)
wxauto-mcp --config

# 生成配置文件到指定目录
wxauto-mcp --config /path/to/configs
```

### 手动配置

如果需要手动配置，运行：

```bash
wxauto-mcp --config mcp-configs
```

然后将生成的配置文件内容添加到 AI 应用中：

**Claude Desktop** 配置文件位置：
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Claude Code** 配置文件位置：
- `%USERPROFILE%\.claude.json`

**Cursor**：在 Settings 的 MCP 配置中添加

### 启动服务器

```bash
# stdio 模式 (默认，用于 MCP 客户端)
wxauto-mcp

# HTTP/SSE 模式
wxauto-mcp-http --port 8000

# 指定主机和端口
wxauto-mcp-http --host 0.0.0.0 --port 9000
```

## 可用工具（27个）

### 系统工具（6个）
- `wechat_initialize` - 初始化微信连接
- `wechat_status` - 获取微信运行状态
- `wechat_activate` - 激活 wxautox4
- `wechat_check_activation` - 检查激活状态
- `wechat_list_tools` - 列出所有可用工具
- `get_my_info` - 获取我的微信账号信息

### 消息工具（6个）
- `send_message` - 发送文本消息
- `send_url_card` - 发送链接卡片
- `get_messages` - 获取当前聊天消息
- `get_history` - 获取历史消息
- `get_next_new_message` - 获取下一个聊天窗口的新消息
- `send_bulk_messages` - 批量发送消息

### 联系人工具（3个）
- `get_friends` - 获取好友列表
- `get_chat_info` - 获取当前聊天信息
- `switch_chat` - 切换聊天窗口

### 会话工具（4个）
- `get_sessions` - 获取会话列表
- `get_recent_groups` - 获取最近群聊
- `filter_sessions` - 筛选会话列表
- `get_unread_sessions` - 获取有未读消息的会话

### 文件工具（4个）
- `send_files` - 发送文件
- `send_image` - 发送图片
- `send_directory_files` - 发送整个目录的文件
- `check_file_exists` - 检查文件是否存在

### 好友请求工具（3个）
- `get_new_friends` - 获取新的好友请求列表
- `accept_new_friend` - 接受新的好友请求
- `add_friend` - 添加新好友

### 界面工具（1个）
- `switch_to_contact` - 切换到联系人页面

## 项目结构

```
wxauto-mcp/
├── src/wxauto_mcp/          # MCP 服务器实现
│   └── wxauto_mcp/
│       ├── __init__.py       # 模块入口
│       ├── rpc.py            # MCP RPC 基础设施
│       ├── api_*.py          # API 实现
│       └── utils.py          # 工具函数
├── core/                     # 核心功能
│   ├── wechat_wrapper.py    # wxautox4 封装
│   ├── listener.py          # 消息监听
│   ├── models.py            # 数据模型
│   └── config.py            # 配置管理
├── tests/                    # 测试文件
├── README.md                # 本文档
├── LICENSE                  # MIT 许可证
└── pyproject.toml           # 项目配置
```

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/
```

## 架构设计

本项目基于 [ida-pro-mcp](https://github.com/mrexodia/ida-pro-mcp) 的架构设计：

- **模块化 API**: 按功能划分独立的 API 模块
- **装饰器注册**: 使用 `@tool` 和 `@resource` 装饰器自动注册
- **输出限制**: 自动限制工具输出长度 (50000 字符)
- **多传输支持**: 支持 stdio、HTTP/SSE 传输方式
- **类型安全**: 使用 Pydantic 进行数据验证

## 依赖项

- `mcp>=1.0.0` - Model Context Protocol SDK
- `wxautox4>=0.2.0` - 微信自动化库
- `fastapi>=0.115.0` - HTTP 服务器
- `uvicorn[standard]>=0.32.0` - ASGI 服务器
- `sse-starlette>=2.1.0` - SSE 支持
- `pydantic>=2.0.0` - 数据验证

## HTTP/SSE 模式

MCP Server 支持 HTTP/SSE 传输模式，适用于需要通过网络访问的场景。

### 全局单例机制

**重要**: wxauto-mcp 实现了全局单例机制，确保同一台电脑上只有一个服务器实例运行。

#### 工作原理

1. **自动检测**: 当启动 HTTP/SSE 模式时，会自动检查是否已有实例运行
2. **智能复用**: 如果检测到运行中的实例，新启动会自动退出并提示复用现有实例
3. **避免冲突**: 防止多个实例同时操作微信导致冲突

#### 检查服务器状态

```bash
# 检查默认端口 (8181) 的服务器状态
wxauto-mcp --status

# 检查指定端口的服务器状态
wxauto-mcp --status --port 9000

# 使用管理工具检查状态
wxauto-mcpctl status
```

#### 多个 AI 应用共享服务器

由于单例机制，多个 AI 应用（Claude Desktop、Claude Code、Cursor等）可以安全地共享同一个 wxauto-mcp 服务器：

1. **启动第一个 AI 应用** - 自动启动 wxauto-mcp 服务器
2. **启动其他 AI 应用** - 自动检测并复用已存在的服务器
3. **避免资源浪费** - 只运行一个服务器实例
4. **避免操作冲突** - 只有一个进程操作微信 UI

**配置建议**: 所有 AI 应用配置中使用相同的 URL（默认 `http://localhost:8181/sse`）

### 可用端点

当使用 `wxauto-mcp-http` 启动服务后，以下端点可用：

- `GET /` - 服务器信息
- `GET /health` - 健康检查
- `GET /sse` - SSE 端点（MCP 协议通信）
- `POST /messages/?session_id=<id>` - 消息端点（MCP 协议通信）

### 使用示例

```bash
# 启动 HTTP 服务器（默认端口 8000）
wxauto-mcp-http

# 指定端口
wxauto-mcp-http --port 9000

# 指定监听地址
wxauto-mcp-http --host 0.0.0.0 --port 8000
```

### MCP 客户端配置

对于 HTTP/SSE 模式，需要在 MCP 客户端配置中使用 `url` 字段：

```json
{
  "mcpServers": {
    "wxauto": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## 常见问题

### 1. 激活

wxautox4 需要激活使用。请访问 https://wxauto.org 获取激活密钥，然后：

```bash
# 设置环境变量
set WECHAT_LICENSE_KEY=your-license-key

# 或调用激活工具
wxauto-mcp-http
# 然后调用 wechat_activate 工具
```

### 2. 权限问题

确保 Python 有访问微信进程的权限，建议以管理员身份运行。

### 3. 微信窗口

某些操作需要微信窗口在前台可见，请确保微信窗口未被最小化。

### 4. 配置文件位置

不同 AI 工具的配置文件位置：

**Claude Desktop:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Claude Code:**
- Windows: `%USERPROFILE%\.claude.json`

**Cursor:**
- 在 Settings → MCP 中添加配置

## 联系方式

- GitHub Issues: louxinghao@gmail.com

## 快速开始

### 基础使用

```python
from core import get_wechat

# 获取 WeChat 实例
wx = get_wechat()

# 检查状态
status = wx.get_status()
if status.is_online:
    print(f"微信在线: {status.account_name}")

# 发送消息
wx.chat_with("张三")
wx.send_message("你好!")
```

### 发送文件

```python
# 发送单个文件
wx.send_files("C:/path/to/file.pdf", who="张三")

# 发送多个文件
files = ["file1.pdf", "file2.jpg"]
wx.send_files(files, who="张三")
```

### 获取会话列表

```python
sessions = wx.get_sessions()
for session in sessions:
    print(f"{session.name} ({session.time})")
```

## 错误处理

```python
from core import get_wechat
from core.exceptions import OfflineError, ChatNotFoundError

wx = get_wechat()

try:
    result = wx.chat_with("张三")
    if not result.success:
        print(f"切换失败: {result.message}")
except OfflineError:
    print("微信未运行")
except ChatNotFoundError as e:
    print(f"找不到聊天: {e}")
```

## 配置选项

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `WECHAT_LICENSE_KEY` | 激活密钥 | - |
| `WECHAT_RESIZE` | 自动调整窗口 | True |
| `WECHAT_DEBUG` | 调试模式 | False |
| `WECHAT_LOG_LEVEL` | 日志级别 | INFO |
