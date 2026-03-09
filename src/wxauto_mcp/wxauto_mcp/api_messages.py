"""
消息 API 模块
提供发送消息、获取消息等消息相关操作
"""

import logging
from typing import Optional

from .rpc import tool
from .utils import format_result, format_list, truncate_text

logger = logging.getLogger(__name__)

# 导入 WeChatWrapper
try:
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from core.wechat_wrapper import get_wechat
    from core.models import MessageInfo, MessageType

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


@tool(
    name="send_message",
    description="发送文本消息。参数: msg (消息内容), who (接收人，可选), at (@对象，可选), exact (精确匹配，默认false)"
)
def send_message(
    msg: str,
    who: Optional[str] = None,
    at: Optional[str] = None,
    exact: bool = False
) -> str:
    """
    发送文本消息

    Args:
        msg: 消息内容
        who: 接收人名称，不指定则发送给当前聊天
        at: @对象，支持逗号分隔的多个@
        exact: 搜索联系人时是否精确匹配

    Returns:
        JSON 格式的发送结果
    """
    if not msg:
        return format_result(False, "消息内容不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        # 解析 @ 列表
        at_list = None
        if at:
            at_list = [a.strip() for a in at.split(",") if a.strip()]

        result = wrapper.send_message(msg=msg, who=who, at=at_list, exact=exact)
        return format_result(result.success, result.message, result.data)
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return format_result(False, f"发送消息失败: {e}")


@tool(
    name="get_messages",
    description="获取当前聊天窗口的所有消息"
)
def get_messages() -> str:
    """
    获取当前聊天消息

    Returns:
        JSON 格式的消息列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        messages = wrapper.get_all_messages()
        if not messages:
            return format_result(True, "当前聊天无消息", {"messages": []})

        # 限制消息数量，避免输出过长
        max_messages = 50
        display_messages = messages[:max_messages]

        formatted = []
        for msg in display_messages:
            formatted.append({
                "sender": msg.sender,
                "content": truncate_text(msg.content, 200),
                "type": msg.msg_type.value if isinstance(msg.msg_type, MessageType) else str(msg.msg_type),
                "attr": msg.attr.value if isinstance(msg.attr, MessageType) else str(msg.attr),
            })

        result = {
            "messages": formatted,
            "total": len(messages),
            "displayed": len(display_messages),
            "truncated": len(messages) > max_messages
        }

        return format_result(True, f"获取成功，共 {len(messages)} 条消息", result)
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        return format_result(False, f"获取消息失败: {e}")


@tool(
    name="get_history",
    description="获取历史消息。参数: n (获取数量，默认50)"
)
def get_history(n: int = 50) -> str:
    """
    获取历史消息

    Args:
        n: 获取消息数量

    Returns:
        JSON 格式的消息列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        messages = wrapper.get_history_messages(n=n)
        if not messages:
            return format_result(True, "无历史消息", {"messages": []})

        formatted = []
        for msg in messages:
            formatted.append({
                "sender": msg.sender,
                "content": truncate_text(msg.content, 200),
                "type": msg.msg_type.value if isinstance(msg.msg_type, MessageType) else str(msg.msg_type),
            })

        return format_result(True, f"获取成功，共 {len(messages)} 条消息", {"messages": formatted})
    except Exception as e:
        logger.error(f"获取历史消息失败: {e}")
        return format_result(False, f"获取历史消息失败: {e}")


@tool(
    name="send_bulk_messages",
    description="批量发送消息。参数: messages (JSON数组，每项包含msg和who)"
)
def send_bulk_messages(messages: str) -> str:
    """
    批量发送消息

    Args:
        messages: JSON 格式的消息列表，格式: [{"msg": "内容", "who": "接收人"}]

    Returns:
        JSON 格式的发送结果
    """
    import json

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        msg_list = json.loads(messages)
        if not isinstance(msg_list, list):
            return format_result(False, "messages 参数必须是数组")

        results = []
        success_count = 0

        for item in msg_list:
            if not isinstance(item, dict) or "msg" not in item:
                results.append({"success": False, "error": "无效的消息格式"})
                continue

            result = wrapper.send_message(
                msg=item["msg"],
                who=item.get("who"),
                exact=item.get("exact", False)
            )
            results.append({
                "msg": item["msg"][:50] + "..." if len(item["msg"]) > 50 else item["msg"],
                "who": item.get("who"),
                "success": result.success,
                "message": result.message
            })

            if result.success:
                success_count += 1

        return format_result(
            True,
            f"批量发送完成: {success_count}/{len(msg_list)} 成功",
            {"results": results}
        )
    except json.JSONDecodeError as e:
        return format_result(False, f"JSON 解析失败: {e}")
    except Exception as e:
        logger.error(f"批量发送失败: {e}")
        return format_result(False, f"批量发送失败: {e}")


@tool(
    name="send_url_card",
    description="发送链接卡片。参数: url (链接地址，必填), friends (发送对象，单个名称或列表，可选), message (附加消息，可选), timeout (等待时间，默认10秒)"
)
def send_url_card(
    url: str,
    friends: Optional[str] = None,
    message: Optional[str] = None,
    timeout: int = 10
) -> str:
    """
    发送链接卡片

    Args:
        url: 链接地址（必填）
        friends: 发送对象，可以是单个用户名或用户名列表，逗号分隔（可选）
        message: 附加消息（可选）
        timeout: 等待时间（秒，默认10）

    Returns:
        JSON 格式的发送结果
    """
    if not url:
        return format_result(False, "链接地址不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        # 解析 friends 列表
        friends_list = None
        if friends:
            friends_list = [f.strip() for f in friends.split(",") if f.strip()]
            # 如果只有一个，去掉列表格式
            if len(friends_list) == 1:
                friends_list = friends_list[0]

        # 调用 SendUrlCard 方法
        response = wrapper.wx.SendUrlCard(
            url=url,
            friends=friends_list,
            message=message,
            timeout=timeout
        )

        # 检查响应
        if hasattr(response, 'success') and response.success:
            return format_result(
                True,
                f"链接卡片发送成功: {url}",
                {"url": url, "friends": friends_list, "message": message}
            )
        else:
            error_msg = getattr(response, 'message', '发送失败')
            return format_result(False, f"发送链接卡片失败: {error_msg}")

    except Exception as e:
        logger.error(f"发送链接卡片失败: {e}")
        return format_result(False, f"发送链接卡片失败: {e}")


@tool(
    name="get_next_new_message",
    description="获取下一个聊天窗口的新消息。参数: filter_mute (是否过滤消息免打扰，默认false)"
)
def get_next_new_message(filter_mute: bool = False) -> str:
    """
    获取下一个聊天窗口的新消息

    Args:
        filter_mute: 是否过滤消息免打扰的会话

    Returns:
        JSON 格式的消息列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        # 调用 GetNextNewMessage 方法
        messages_dict = wrapper.wx.GetNextNewMessage(filter_mute=filter_mute)

        if not messages_dict:
            return format_result(True, "无新消息", {"messages": {}})

        # 格式化结果
        formatted = {}
        for chat_name, msg_list in messages_dict.items():
            if isinstance(msg_list, list):
                formatted_msgs = []
                for msg in msg_list[:50]:  # 限制每个聊天最多50条消息
                    formatted_msgs.append({
                        "type": getattr(msg, 'type', 'unknown'),
                        "content": getattr(msg, 'content', ''),
                        "sender": getattr(msg, 'sender', ''),
                        "time": getattr(msg, 'time', ''),
                    })
                formatted[chat_name] = formatted_msgs

        return format_result(
            True,
            f"获取成功，共 {len(formatted)} 个聊天有新消息",
            {"messages": formatted}
        )

    except Exception as e:
        logger.error(f"获取新消息失败: {e}")
        return format_result(False, f"获取新消息失败: {e}")
