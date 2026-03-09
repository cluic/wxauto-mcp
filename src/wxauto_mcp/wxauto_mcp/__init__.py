"""
wxauto MCP Server
微信自动化模型上下文协议服务器

提供基于 MCP 协议的微信自动化 API，支持 Claude Code、Cursor 等 AI 开发工具。
"""

__version__ = "1.0.0"
__author__ = "wxauto MCP Team"

# 导入 RPC 模块
from .rpc import MCP_SERVER, tool, resource

# 导入 API 模块（必须导入才能让装饰器执行）
from . import api_messages
from . import api_contacts
from . import api_sessions
from . import api_files
from . import api_listen
from . import api_system
from . import api_friends

__all__ = [
    "MCP_SERVER",
    "tool",
    "resource",
    "api_messages",
    "api_contacts",
    "api_sessions",
    "api_files",
    "api_listen",
    "api_system",
    "api_friends",
]
