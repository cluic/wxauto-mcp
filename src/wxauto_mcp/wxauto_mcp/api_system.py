"""
系统 API 模块
提供微信状态检查、激活管理等系统级操作
"""

import logging
import os
from typing import Optional

from .rpc import tool
from .utils import format_result

logger = logging.getLogger(__name__)

# 尝试导入 WeChatWrapper
try:
    import sys
    from pathlib import Path

    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from core.wechat_wrapper import WeChatWrapper, get_wechat
    from core.models import WeChatStatus

    WECHAT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法导入 WeChatWrapper: {e}")
    WECHAT_AVAILABLE = False
    WeChatWrapper = None
    get_wechat = None
    WeChatStatus = None


def _get_wrapper() -> Optional["WeChatWrapper"]:
    """获取 WeChatWrapper 实例"""
    if not WECHAT_AVAILABLE:
        return None
    try:
        return get_wechat()
    except Exception as e:
        logger.error(f"获取 WeChat 实例失败: {e}")
        return None


@tool(
    name="wechat_status",
    description="获取微信运行状态，包括在线状态、账号信息和激活状态"
)
def wechat_status() -> str:
    """
    获取微信状态

    Returns:
        JSON 格式的状态信息
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        status = wrapper.get_status()
        return format_result(
            True,
            "获取状态成功",
            {
                "is_online": status.is_online,
                "account_name": status.account_name,
                "account_id": status.account_id,
                "is_activated": status.is_activated,
            },
        )
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return format_result(False, f"获取状态失败: {e}")


@tool(
    name="wechat_initialize",
    description="初始化微信连接。参数: resize (是否自动调整窗口，默认true), debug (调试模式，默认false)"
)
def wechat_initialize(resize: bool = True, debug: bool = False) -> str:
    """
    初始化微信

    Args:
        resize: 是否自动调整窗口尺寸
        debug: 是否开启调试模式

    Returns:
        JSON 格式的初始化结果
    """
    if not WECHAT_AVAILABLE:
        return format_result(False, "wxautox4 未安装或导入失败")

    try:
        # 创建 wrapper 实例以检查激活状态
        wrapper = get_wechat()

        # 检查激活状态
        is_activated = wrapper.check_activation()
        if not is_activated:
            return format_result(
                False,
                "wxautox4 未激活，请先调用 wechat_activate 方法激活。"
                "您需要设置 WECHAT_LICENSE_KEY 环境变量或调用 wechat_activate 方法提供激活密钥。",
                {"is_activated": False, "hint": "调用 wechat_activate(license_key='your-key') 激活"}
            )

        # 调用初始化方法（如果已经初始化过会直接返回成功）
        result = wrapper.initialize(resize=resize, debug=debug)

        if result.success:
            return format_result(True, "微信初始化成功")
        else:
            return format_result(False, f"初始化失败: {result.message}")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return format_result(False, f"初始化失败: {e}")


@tool(
    name="wechat_activate",
    description="激活 wxautox4。参数: license_key (激活密钥，留空则使用环境变量 WECHAT_LICENSE_KEY)"
)
def wechat_activate(license_key: Optional[str] = None) -> str:
    """
    激活 wxautox4

    Args:
        license_key: 激活密钥

    Returns:
        JSON 格式的激活结果
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        result = wrapper.activate(license_key)
        return format_result(result.success, result.message, result.data)
    except Exception as e:
        logger.error(f"激活失败: {e}")
        return format_result(False, f"激活失败: {e}")


@tool(
    name="wechat_check_activation",
    description="检查 wxautox4 激活状态"
)
def wechat_check_activation() -> str:
    """
    检查激活状态

    Returns:
        JSON 格式的激活状态
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        is_activated = wrapper.check_activation()
        return format_result(True, "检查完成", {"is_activated": is_activated})
    except Exception as e:
        logger.error(f"检查激活状态失败: {e}")
        return format_result(False, f"检查失败: {e}")


@tool(
    name="wechat_list_tools",
    description="列出所有可用的微信自动化工具"
)
def wechat_list_tools() -> str:
    """
    列出所有可用工具

    Returns:
        工具列表
    """
    tools = {
        "系统工具": [
            "wechat_status - 获取微信状态",
            "wechat_initialize - 初始化微信",
            "wechat_activate - 激活 wxautox4",
            "wechat_check_activation - 检查激活状态",
        ],
        "消息工具": [
            "send_message - 发送文本消息",
            "get_messages - 获取当前聊天消息",
            "get_history - 获取历史消息",
        ],
        "联系人工具": [
            "get_friends - 获取好友列表",
            "get_chat_info - 获取当前聊天信息",
            "switch_chat - 切换聊天窗口",
        ],
        "会话工具": [
            "get_sessions - 获取会话列表",
            "get_recent_groups - 获取最近群聊",
        ],
        "文件工具": [
            "send_files - 发送文件",
            "send_image - 发送图片",
        ],
    }

    lines = ["可用的微信自动化工具:"]
    for category, items in tools.items():
        lines.append(f"\n{category}:")
        for item in items:
            lines.append(f"  - {item}")

    return "\n".join(lines)


@tool(
    name="get_my_info",
    description="获取我的微信账号信息"
)
def get_my_info() -> str:
    """
    获取我的微信账号信息

    Returns:
        JSON 格式的账号信息
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        my_info = wrapper.wx.GetMyInfo()
        if not my_info:
            return format_result(False, "无法获取账号信息")

        return format_result(True, "获取成功", my_info)
    except Exception as e:
        logger.error(f"获取账号信息失败: {e}")
        return format_result(False, f"获取账号信息失败: {e}")


@tool(
    name="switch_to_contact",
    description="切换微信到联系人页面"
)
def switch_to_contact() -> str:
    """
    切换到联系人页面

    Returns:
        JSON 格式的操作结果
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        wrapper.wx.SwitchToContact()
        return format_result(True, "已切换到联系人页面")
    except Exception as e:
        logger.error(f"切换页面失败: {e}")
        return format_result(False, f"切换页面失败: {e}")
