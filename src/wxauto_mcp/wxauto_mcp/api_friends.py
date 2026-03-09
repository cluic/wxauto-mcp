"""
好友请求 API 模块
提供处理好友请求、添加新好友等操作
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

    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from wxauto_mcp.core.wechat_wrapper import get_wechat

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
    name="get_new_friends",
    description="获取新的好友请求列表。参数: acceptable (是否过滤掉已接受的好友申请，默认true)"
)
def get_new_friends(acceptable: bool = True) -> str:
    """
    获取新的好友请求

    Args:
        acceptable: 是否过滤掉已接受的好友申请

    Returns:
        JSON 格式的新好友请求列表
    """
    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化，请先调用 wechat_initialize")

    try:
        # 调用 wxauto 的 GetNewFriends 方法
        new_friends = wrapper.wx.GetNewFriends(acceptable=acceptable)

        # 切换回聊天页面
        try:
            wrapper.wx.SwitchToChat()
        except:
            pass  # 如果切换失败，不影响主要功能

        if not new_friends:
            return format_result(True, "暂无新的好友请求", {"friends": []})

        # 格式化结果
        formatted = []
        for friend in new_friends:
            # NewFriendElement 对象的属性
            friend_info = {
                "content": friend.content
            }
            formatted.append(friend_info)

        return format_result(
            True,
            f"获取成功，共 {len(new_friends)} 个新的好友请求",
            {"friends": formatted}
        )
    except AttributeError:
        return format_result(False, "当前微信版本不支持 GetNewFriends 方法，请升级微信或 wxautox4 版本")
    except Exception as e:
        logger.error(f"获取新好友请求失败: {e}")
        return format_result(False, f"获取新好友请求失败: {e}")


@tool(
    name="accept_new_friend",
    description="接受新的好友请求。参数: content (好友请求内容，必填), exact (是否精确匹配，默认false), remark (备注名，可选), tags (标签列表，可选)"
)
def accept_new_friend(content: str, exact: bool = False, remark: Optional[str] = None, tags: Optional[list[str]] = None) -> str:
    """
    接受新的好友请求

    Args:
        content: 好友请求内容（必填）
        exact: 是否精确匹配，默认 false（模糊匹配，包含即可）
        remark: 备注名（可选）
        tags: 标签列表（可选）

    Returns:
        JSON 格式的操作结果
    """
    if not content:
        return format_result(False, "好友请求内容不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        # 获取新的好友请求列表
        new_friends = wrapper.wx.GetNewFriends(acceptable=True)

        if not new_friends:
            return format_result(False, "暂无新的好友请求")

        # 查找对应的好友请求
        found = False
        matched_content = None
        for friend in new_friends:
            friend_content = getattr(friend, 'content', '')

            # 根据 exact 参数决定匹配方式
            if exact:
                # 精确匹配
                if content == friend_content:
                    matched_content = friend_content
                    found = True
                    break
            else:
                # 模糊匹配（包含即可）
                if content in friend_content:
                    matched_content = friend_content
                    found = True
                    break

        if found:
            # 调用 friend.accept() 方法接受好友请求
            friend.accept(remark=remark or "", tags=tags or [])
            return format_result(
                True,
                f"已接受好友请求: {matched_content[:50]}{'...' if len(matched_content) > 50 else ''}",
                {"content": matched_content, "remark": remark, "tags": tags}
            )
        else:
            # 列出所有可用的好友请求内容，方便用户查找
            available_contents = [getattr(f, 'content', '') for f in new_friends]
            return format_result(
                False,
                f"未找到匹配的好友请求: {content}",
                {"search_content": content, "available_requests": available_contents}
            )

    except Exception as e:
        logger.error(f"接受好友请求失败: {e}")
        return format_result(False, f"接受好友请求失败: {e}")
    
    finally:
        # 切换回聊天页面
        try:
            wrapper.wx.SwitchToChat()
        except:
            pass  # 如果切换失败，不影响主要功能


@tool(
    name="add_friend",
    description="添加新好友。参数: keywords (搜索关键词，必填), addmsg (验证消息，可选), remark (备注名，可选), tags (标签列表，可选), permission (权限，可选：朋友圈/仅聊天，默认朋友圈), timeout (超时时间，默认5秒)"
)
def add_friend(
    keywords: str,
    addmsg: Optional[str] = None,
    remark: Optional[str] = None,
    tags: Optional[list[str]] = None,
    permission: str = "朋友圈",
    timeout: int = 5
) -> str:
    """
    添加新好友

    Args:
        keywords: 搜索关键词，可以是昵称、微信号、手机号等（必填）
        addmsg: 添加好友时的附加消息（可选）
        remark: 添加好友后的备注（可选）
        tags: 添加好友后的标签列表（可选）
        permission: 添加好友后的权限，可选值：'朋友圈' 或 '仅聊天'（默认'朋友圈'）
        timeout: 超时时间（秒，默认5）

    Returns:
        JSON 格式的操作结果
    """
    if not keywords:
        return format_result(False, "搜索关键词不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        # 调用 AddNewFriend 方法
        response = wrapper.wx.AddNewFriend(
            keywords=keywords,
            addmsg=addmsg,
            remark=remark,
            tags=tags or [],
            permission=permission,
            timeout=timeout
        )

        # 切换回聊天页面
        try:
            wrapper.wx.SwitchToChat()
        except:
            pass  # 如果切换失败，不影响主要功能

        # 检查响应
        if hasattr(response, 'success') and response.success:
            return format_result(
                True,
                f"已发送好友请求: {keywords}",
                {"keywords": keywords, "remark": remark, "tags": tags}
            )
        else:
            error_msg = getattr(response, 'message', '添加好友失败')
            return format_result(False, f"添加好友失败: {error_msg}")

    except Exception as e:
        logger.error(f"添加好友失败: {e}")
        return format_result(False, f"添加好友失败: {e}")
