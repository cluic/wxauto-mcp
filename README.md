# wxauto MCP Server

微信自动化 MCP (Model Context Protocol) 服务器，为 AI 开发工具提供微信自动化能力。

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-1.0+-orange.svg)](https://modelcontextprotocol.io/)

## 系统要求

- Windows 11/10
- Python 3.9+
- 微信已登录
- wxautox4 激活


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

### 生成配置文件（手动配置）

如果需要手动配置，运行：

```bash
# 生成配置文件到默认目录 (./mcp-configs)
wxauto-mcp --config

# 生成配置文件到指定目录
wxauto-mcp --config /path/to/configs

wxauto-mcp --config mcp-configs
```

然后将生成的配置文件内容添加到 AI 应用中：

**Claude Desktop** 配置文件位置：
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Claude Code** 配置文件位置：
- `%USERPROFILE%\.claude.json`

**Cursor**：在 Settings 的 MCP 配置中添加


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


## 常见问题

### 1. 激活

wxautox4 需要激活使用。请访问 https://docs.wxauto.org 获取激活密钥，然后：

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
