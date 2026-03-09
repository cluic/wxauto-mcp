"""
会话 API 模块
提供获取会话列表、群聊列表等会话相关操作
"""

import logging
from typing import Optional

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
    from core.models import SessionInfo

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
    name="get_sessions",
    description="获取微信会话列表（聊天窗口列表）"
)
def get_sessions() -> str:
    """
    获取会话列表

    Returns:
        JSON 格式的会话列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        sessions = wrapper.get_sessions()
        if not sessions:
            return format_result(True, "无会话数据", {"sessions": []})

        formatted = []
        for session in sessions:
            formatted.append({
                "name": session.name,
                "time": session.time,
                "content": session.content,
                "isnew": session.isnew,
                "new_count": session.new_count,
                "ismute": session.ismute,
            })

        return format_result(True, f"获取成功，共 {len(sessions)} 个会话", {"sessions": formatted})
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return format_result(False, f"获取会话列表失败: {e}")


@tool(
    name="get_recent_groups",
    description="获取最近群聊列表"
)
def get_recent_groups() -> str:
    """
    获取最近群聊列表

    Returns:
        JSON 格式的群聊列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        groups = wrapper.get_recent_groups()
        if not groups:
            return format_result(True, "无群聊数据", {"groups": []})

        return format_result(
            True,
            f"获取成功，共 {len(groups)} 个群聊",
            {"groups": [{"name": g} for g in groups]}
        )
    except Exception as e:
        logger.error(f"获取群聊列表失败: {e}")
        return format_result(False, f"获取群聊列表失败: {e}")


@tool(
    name="filter_sessions",
    description="筛选会话列表。参数: has_unread (是否有未读), ismute (是否免打扰)"
)
def filter_sessions(
    has_unread: Optional[bool] = None,
    ismute: Optional[bool] = None
) -> str:
    """
    筛选会话列表

    Args:
        has_unread: 是否只显示有未读消息的会话
        ismute: 是否筛选免打扰会话

    Returns:
        JSON 格式的筛选结果
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        sessions = wrapper.get_sessions()
        if not sessions:
            return format_result(True, "无会话数据", {"sessions": []})

        # 应用筛选
        filtered = sessions
        if has_unread is not None:
            if has_unread:
                filtered = [s for s in filtered if s.new_count > 0]
            else:
                filtered = [s for s in filtered if s.new_count == 0]

        if ismute is not None:
            filtered = [s for s in filtered if s.ismute == ismute]

        # 格式化结果
        formatted = []
        for session in filtered:
            formatted.append({
                "name": session.name,
                "time": session.time,
                "content": session.content,
                "new_count": session.new_count,
                "ismute": session.ismute,
            })

        return format_result(
            True,
            f"筛选完成，共 {len(formatted)} 个会话",
            {"sessions": formatted}
        )
    except Exception as e:
        logger.error(f"筛选会话失败: {e}")
        return format_result(False, f"筛选会话失败: {e}")


@tool(
    name="get_unread_sessions",
    description="获取所有有未读消息的会话"
)
def get_unread_sessions() -> str:
    """
    获取有未读消息的会话

    Returns:
        JSON 格式的会话列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        sessions = wrapper.get_sessions()
        unread = [s for s in sessions if s.new_count > 0]

        if not unread:
            return format_result(True, "无未读消息", {"sessions": []})

        formatted = []
        for session in unread:
            formatted.append({
                "name": session.name,
                "time": session.time,
                "content": session.content,
                "new_count": session.new_count,
                "ismute": session.ismute,
            })

        return format_result(
            True,
            f"共 {len(unread)} 个会话有未读消息",
            {"sessions": formatted}
        )
    except Exception as e:
        logger.error(f"获取未读会话失败: {e}")
        return format_result(False, f"获取未读会话失败: {e}")
