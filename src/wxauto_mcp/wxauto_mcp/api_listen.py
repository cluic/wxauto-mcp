"""
监听 API 模块
提供消息监听相关功能（基于 wxautox4 的监听模式）
"""

import logging
from typing import Optional, Callable, Any

from .rpc import tool
from .utils import format_result

logger = logging.getLogger(__name__)

# 导入 WeChatWrapper
try:
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from core.wechat_wrapper import get_wechat

    WECHAT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法导入 WeChatWrapper: {e}")
    WECHAT_AVAILABLE = False
    get_wechat = None


def _get_wrapper():
    """获取 WeChatWrapper 实例"""
    if not WECHAT_AVAILABLE:
        return None
    try:
        return get_wechat()
    except Exception as e:
        logger.error(f"获取 WeChat 实例失败: {e}")
        return None


# 暂时禁用监听功能
# @tool(
#     name="listen_messages",
#     description="监听消息（说明性工具）。参数: nickname (监听的联系人名称)"
# )
def listen_messages(nickname: str = "") -> str:
    """
    消息监听说明

    注意: wxautox4 的消息监听需要阻塞模式运行，MCP Server 不支持长期阻塞。
    此工具提供监听功能的说明和配置建议。

    Args:
        nickname: 要监听的联系人名称

    Returns:
        监听配置说明
    """
    return """
# 微信消息监听功能说明

由于 MCP 协议的限制（基于请求-响应模式），不支持长期阻塞的消息监听。

## 推荐方案

### 方案 1: 轮询模式
定期调用 `get_messages` 或 `get_history` 获取最新消息。

### 方案 2: 独立监听进程
使用 wxautox4 的原生监听功能：

```python
from wxautox4 import WeChat

wx = WeChat()

@wx.msg_register
def on_message(msg):
    print(f"收到消息: {msg.content}")
    # 处理消息逻辑

wx.KeepRunning()  # 阻塞监听
```

### 方案 3: 使用 MCP Resources
创建 MCP Resource 提供消息流数据（待实现）。

## 当前可用工具

- `get_messages` - 获取当前聊天消息
- `get_history` - 获取历史消息
- `get_sessions` - 获取会话列表
- `get_unread_sessions` - 获取未读会话

这些工具可用于构建轮询式的消息监听逻辑。
"""


# 暂时禁用监听功能
# @tool(
#     name="setup_listen_callback",
#     description="设置消息监听回调（需要外部脚本支持）。参数: callback_script (回调脚本路径)"
# )
def setup_listen_callback(callback_script: str = "") -> str:
    """
    设置监听回调

    提供设置独立监听脚本的说明和模板。

    Args:
        callback_script: 回调脚本路径

    Returns:
        配置说明和脚本模板
    """
    template = '''
# 独立消息监听脚本模板

将以下代码保存为 `listen_messages.py` 并独立运行：

```python
import os
import sys
import json
import logging
from datetime import datetime

# 安装 wxautox4: pip install wxautox4
from wxautox4 import WeChat

# 设置激活密钥
os.environ["WECHAT_LICENSE_KEY"] = "your-license-key-here"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wechat_messages.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def save_message(msg):
    """保存消息到文件"""
    message_data = {
        "timestamp": datetime.now().isoformat(),
        "sender": msg.sender,
        "content": msg.content,
        "type": msg.type,
        "chat": msg.chat.get("name") if hasattr(msg, 'chat') else None,
    }

    # 追加到消息日志文件
    with open('messages.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(message_data, ensure_ascii=False) + '\\n')

    logger.info(f"收到消息: {msg.sender} - {msg.content[:50]}...")

def main():
    """主函数"""
    logger.info("启动微信消息监听...")

    try:
        # 创建 WeChat 实例
        wx = WeChat()

        # 注册消息处理器
        @wx.msg_register
        def on_message(msg):
            save_message(msg)

        logger.info("监听已启动，按 Ctrl+C 停止...")
        wx.KeepRunning()

    except KeyboardInterrupt:
        logger.info("监听已停止")
    except Exception as e:
        logger.error(f"监听出错: {e}")

if __name__ == "__main__":
    main()
```

## 使用方法

1. 设置激活密钥环境变量: `export WECHAT_LICENSE_KEY=your-key`
2. 运行脚本: `python listen_messages.py`
3. 消息将保存到 `messages.jsonl` 文件
4. 在 MCP 工具中读取该文件获取最新消息

## 集成到 MCP

可以创建 MCP Resource 读取 `messages.jsonl` 提供消息流。
'''

    return format_result(
        True,
        "监听回调配置说明",
        {
            "template": template,
            "note": "消息监听需要独立进程运行，不受 MCP 协议限制"
        }
    )


# 暂时禁用监听功能
# @tool(
#     name="get_listen_status",
#     description="获取消息监听状态"
# )
def get_listen_status() -> str:
    """
    获取监听状态

    检查独立监听进程的状态。

    Returns:
        JSON 格式的状态信息
    """
    import os
    from pathlib import Path

    # 检查监听相关文件
    message_log = Path("messages.jsonl")
    log_file = Path("wechat_messages.log")

    status = {
        "message_log_exists": message_log.exists(),
        "log_file_exists": log_file.exists(),
        "listener_running": False,
    }

    # 如果消息日志存在，检查最后更新时间
    if status["message_log_exists"]:
        mtime = message_log.stat().st_mtime
        import time
        status["last_update"] = mtime
        status["last_update_seconds_ago"] = time.time() - mtime
        # 如果5分钟内有更新，认为监听器在运行
        status["listener_running"] = (time.time() - mtime) < 300

    return format_result(
        True,
        "状态检查完成",
        status
    )


# 暂时禁用监听功能
# @tool(
#     name="remove_listen_chat",
#     description="移除监听聊天窗口。参数: nickname (要移除的监听聊天对象名称)"
# )
def remove_listen_chat(nickname: str) -> str:
    """
    移除监听聊天窗口

    Args:
        nickname: 要移除的监听聊天对象名称

    Returns:
        JSON 格式的操作结果
    """
    if not nickname:
        return format_result(False, "聊天对象名称不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        # 调用 RemoveListenChat 方法
        response = wrapper.wx.RemoveListenChat(nickname=nickname)

        # 检查响应
        if hasattr(response, 'success') and response.success:
            return format_result(
                True,
                f"已移除监听: {nickname}",
                {"nickname": nickname}
            )
        else:
            error_msg = getattr(response, 'message', '移除失败')
            return format_result(False, f"移除监听失败: {error_msg}")

    except Exception as e:
        logger.error(f"移除监听失败: {e}")
        return format_result(False, f"移除监听失败: {e}")
