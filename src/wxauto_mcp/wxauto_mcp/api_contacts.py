"""
联系人 API 模块
提供获取好友列表、切换聊天等联系人相关操作
"""

import logging
from typing import Optional

from .rpc import tool
from .utils import format_result, format_list

logger = logging.getLogger(__name__)

# 导入 WeChatWrapper
try:
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from core.wechat_wrapper import get_wechat
    from core.models import ContactInfo

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
    name="get_friends",
    description="获取好友列表。参数: n (获取数量，默认10), save_avatar (是否获取头像，默认false)"
)
def get_friends(n: int = 10, save_avatar: bool = False) -> str:
    """
    获取好友列表

    Args:
        n: 获取数量
        save_avatar: 是否获取头像

    Returns:
        JSON 格式的好友列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        friends = wrapper.get_friend_details(n=n, save_head_image=save_avatar)

        # 切换回聊天页面（GetFriendDetails 会切换到联系人页面）
        try:
            wrapper.wx.SwitchToChat()
        except:
            pass  # 如果切换失败，不影响主要功能

        if not friends:
            return format_result(True, "无好友数据", {"friends": []})

        formatted = []
        for friend in friends:
            formatted.append({
                "name": friend.name,
                "alias": friend.alias,
                "remark": friend.remark,
                "signature": friend.signature,
                "source": friend.source,
            })

        return format_result(True, f"获取成功，共 {len(friends)} 个好友", {"friends": formatted})
    except Exception as e:
        logger.error(f"获取好友列表失败: {e}")
        return format_result(False, f"获取好友列表失败: {e}")


@tool(
    name="switch_chat",
    description="切换到指定聊天窗口。参数: who (联系人名称), exact (精确匹配，默认false)"
)
def switch_chat(who: str, exact: bool = False) -> str:
    """
    切换聊天窗口

    Args:
        who: 联系人名称
        exact: 是否精确匹配

    Returns:
        JSON 格式的切换结果
    """
    if not who:
        return format_result(False, "联系人名称不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        result = wrapper.chat_with(who=who, exact=exact)
        return format_result(result.success, result.message, result.data)
    except Exception as e:
        logger.error(f"切换聊天失败: {e}")
        return format_result(False, f"切换聊天失败: {e}")


@tool(
    name="get_chat_info",
    description="获取当前聊天窗口信息"
)
def get_chat_info() -> str:
    """
    获取当前聊天信息

    Returns:
        JSON 格式的聊天信息
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        info = wrapper.get_chat_info()
        if not info:
            return format_result(False, "无法获取聊天信息")

        return format_result(True, "获取成功", {"chat_info": info})
    except Exception as e:
        logger.error(f"获取聊天信息失败: {e}")
        return format_result(False, f"获取聊天信息失败: {e}")
