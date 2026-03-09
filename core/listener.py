"""
消息监听器实现
提供消息监听、关键词过滤、回调管理等功能
"""

import logging
import threading
from typing import Optional, , Callable, , Any, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

try:
    from wxautox4.msgs import BaseMessage
    from wxautox4 import Chat
    WXAUTO_AVAILABLE = True
except ImportError:
    WXAUTO_AVAILABLE = False
    BaseMessage = None
    Chat = None

# 导入本地模型
from .models import (
    MessageInfo, MessageType, MessageAttribute,
    ListenConfig, MessageResult, ChatType
)


# 配置日志
logger = logging.getLogger(__name__)


class CallbackPriority(int, Enum):
    """回调优先级"""
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class CallbackEntry:
    """
    回调条目

    Attributes:
        func: 回调函数
        priority: 优先级
        enabled: 是否启用
        name: 回调名称
    """
    func: Callable[[Any, Any], None]
    priority: CallbackPriority = CallbackPriority.NORMAL
    enabled: bool = True
    name: str = ""
    filter_types: list[MessageType] = field(default_factory=list)
    filter_keywords: list[str] = field(default_factory=list)

    def should_trigger(self, msg_info: MessageInfo) -> bool:
        """
        判断是否应该触发回调

        Args:
            msg_info: 消息信息

        Returns:
            bool: 是否触发
        """
        if not self.enabled:
            return False

        # 消息类型过滤
        if self.filter_types and msg_info.msg_type not in self.filter_types:
            return False

        # 关键词过滤
        if self.filter_keywords:
            content_lower = msg_info.content.lower()
            if not any(kw.lower() in content_lower for kw in self.filter_keywords):
                return False

        return True


class MessageListener:
    """
    消息监听器

    管理多个监听会话和回调函数，提供线程安全的消息处理。

    Attributes:
        _wrapper: WeChatWrapper 实例
        _callbacks: 回调列表
        _listen_chats: 监听的聊天
        _lock: 线程锁
        _executor: 线程池
    """

    def __init__(self, wrapper):
        """
        初始化监听器

        Args:
            wrapper: WeChatWrapper 实例
        """
        if not WXAUTO_AVAILABLE:
            raise ImportError("wxautox4 未安装")

        self._wrapper = wrapper
        self._callbacks: list[CallbackEntry] = []
        self._listen_chats: dict[str, Chat] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="msg_listener")
        self._running = False
        self._message_count = 0

        logger.info("MessageListener 初始化完成")

    def add_listen_chat(
        self,
        nickname: str,
        callback: Optional[Callable[[Any, Any], None]] = None,
        keywords: Optional[list[str]] = None,
        msg_types: Optional[list[MessageType]] = None
    ) -> MessageResult:
        """
        添加监听聊天

        Args:
            nickname: 联系人名称
            callback: 消息回调函数 (msg, chat) -> None
            keywords: 关键词过滤列表
            msg_types: 消息类型过滤列表

        Returns:
            MessageResult: 添加结果
        """
        try:
            # 如果提供了回调，先注册
            if callback:
                self.add_callback(
                    func=callback,
                    name=f"listen_{nickname}",
                    filter_keywords=keywords or [],
                    filter_types=msg_types or []
                )

            # 添加监听
            with self._lock:
                result = self._wrapper.wx.AddListenChat(
                    nickname=nickname,
                    callback=self._create_wrapper_callback(nickname)
                )

                if isinstance(result, Chat):
                    self._listen_chats[nickname] = result
                    logger.info(f"添加监听成功: {nickname}")
                    return MessageResult.from_success(
                        f"添加监听成功: {nickname}",
                        data={"nickname": nickname}
                    )
                else:
                    return MessageResult.from_error(
                        f"添加监听失败: {nickname}",
                        SendStatus.FAILED
                    )
        except Exception as e:
            logger.error(f"添加监听失败 {nickname}: {e}")
            return MessageResult.from_error(f"添加监听失败: {e}")

    def remove_listen_chat(self, nickname: str) -> MessageResult:
        """
        移除监听聊天

        Args:
            nickname: 联系人名称

        Returns:
            MessageResult: 移除结果
        """
        try:
            with self._lock:
                if nickname in self._listen_chats:
                    del self._listen_chats[nickname]

                result = self._wrapper.wx.RemoveListenChat(nickname=nickname)

                if hasattr(result, 'success') and not result.success:
                    return MessageResult.from_error(
                        result.message or "移除失败",
                        SendStatus.FAILED
                    )

                logger.info(f"移除监听成功: {nickname}")
                return MessageResult.from_success(f"移除监听成功: {nickname}")

        except Exception as e:
            logger.error(f"移除监听失败 {nickname}: {e}")
            return MessageResult.from_error(f"移除监听失败: {e}")

    def _create_wrapper_callback(self, nickname: str):
        """
        创建包装回调函数

        Args:
            nickname: 联系人名称

        Returns:
            Callable: 回调函数
        """
        def wrapper_callback(msg: BaseMessage, chat: Chat):
            """内部包装回调"""
            try:
                # 转换为 MessageInfo
                msg_info = self._convert_message(msg, nickname)

                # 更新计数
                with self._lock:
                    self._message_count += 1

                # 异步执行所有回调
                self._execute_callbacks(msg_info, msg, chat)

            except Exception as e:
                logger.error(f"处理消息回调失败 {nickname}: {e}")

        return wrapper_callback

    def _convert_message(self, msg: BaseMessage, chat_name: str) -> MessageInfo:
        """
        转换消息为 MessageInfo

        Args:
            msg: wxautox4 消息对象
            chat_name: 聊天名称

        Returns:
            MessageInfo: 消息信息
        """
        msg_type = MessageType.TEXT
        try:
            if msg.type in MessageType.__members__:
                msg_type = MessageType(msg.type)
        except (ValueError, AttributeError):
            pass

        msg_attr = MessageAttribute.FRIEND
        try:
            if msg.attr in MessageAttribute.__members__:
                msg_attr = MessageAttribute(msg.attr)
        except (ValueError, AttributeError):
            pass

        return MessageInfo(
            content=msg.content,
            sender=msg.sender,
            msg_type=msg_type,
            attr=msg_attr,
            chat_name=chat_name
        )

    def _execute_callbacks(self, msg_info: MessageInfo, msg: BaseMessage, chat: Chat):
        """
        执行所有符合条件的回调

        Args:
            msg_info: 消息信息
            msg: 原始消息
            chat: 聊天对象
        """
        with self._lock:
            callbacks = [cb for cb in self._callbacks if cb.should_trigger(msg_info)]

        # 按优先级排序
        callbacks.sort(key=lambda x: x.priority)

        for cb in callbacks:
            try:
                # 在线程池中异步执行
                self._executor.submit(cb.func, msg, chat)
            except Exception as e:
                logger.error(f"执行回调失败 {cb.name}: {e}")

    def add_callback(
        self,
        func: Callable[[Any, Any], None],
        name: str = "",
        priority: CallbackPriority = CallbackPriority.NORMAL,
        filter_keywords: Optional[list[str]] = None,
        filter_types: Optional[list[MessageType]] = None,
        enabled: bool = True
    ) -> str:
        """
        添加全局回调函数

        Args:
            func: 回调函数 (msg, chat) -> None
            name: 回调名称
            priority: 优先级
            filter_keywords: 关键词过滤
            filter_types: 消息类型过滤
            enabled: 是否启用

        Returns:
            str: 回调ID
        """
        callback_id = name or f"callback_{id(func)}"

        with self._lock:
            entry = CallbackEntry(
                func=func,
                priority=priority,
                enabled=enabled,
                name=callback_id,
                filter_keywords=filter_keywords or [],
                filter_types=filter_types or []
            )
            self._callbacks.append(entry)

        logger.info(f"添加回调: {callback_id}")
        return callback_id

    def remove_callback(self, callback_id: str) -> bool:
        """
        移除回调函数

        Args:
            callback_id: 回调ID

        Returns:
            bool: 是否移除成功
        """
        with self._lock:
            for i, cb in enumerate(self._callbacks):
                if cb.name == callback_id:
                    self._callbacks.pop(i)
                    logger.info(f"移除回调: {callback_id}")
                    return True
            return False

    def enable_callback(self, callback_id: str) -> bool:
        """启用回调"""
        with self._lock:
            for cb in self._callbacks:
                if cb.name == callback_id:
                    cb.enabled = True
                    return True
            return False

    def disable_callback(self, callback_id: str) -> bool:
        """禁用回调"""
        with self._lock:
            for cb in self._callbacks:
                if cb.name == callback_id:
                    cb.enabled = False
                    return True
            return False

    def get_listen_chats(self) -> list[str]:
        """
        获取监听的聊天列表

        Returns:
            list[str]: 聊天名称列表
        """
        with self._lock:
            return list(self._listen_chats.keys())

    def get_callback_list(self) -> list[dict[str, Any]]:
        """
        获取回调列表

        Returns:
            list[Dict]: 回调信息列表
        """
        with self._lock:
            return [
                {
                    "name": cb.name,
                    "priority": cb.priority.value,
                    "enabled": cb.enabled,
                    "filter_keywords": cb.filter_keywords,
                    "filter_types": [t.value for t in cb.filter_types]
                }
                for cb in self._callbacks
            ]

    def get_message_count(self) -> int:
        """
        获取已处理消息数量

        Returns:
            int: 消息数量
        """
        with self._lock:
            return self._message_count

    def reset_message_count(self):
        """重置消息计数"""
        with self._lock:
            self._message_count = 0

    def get_listen_messages(self) -> list[MessageInfo]:
        """
        获取监听到的消息

        Returns:
            list[MessageInfo]: 消息列表
        """
        try:
            messages = self._wrapper.wx.GetListenMessage()
            result = []
            for msg in messages:
                # 转换消息
                msg_type = MessageType.TEXT
                if hasattr(msg, 'type') and msg.type in MessageType.__members__:
                    msg_type = MessageType(msg.type)

                msg_attr = MessageAttribute.FRIEND
                if hasattr(msg, 'attr') and msg.attr in MessageAttribute.__members__:
                    msg_attr = MessageAttribute(msg.attr)

                result.append(MessageInfo(
                    content=msg.content,
                    sender=msg.sender,
                    msg_type=msg_type,
                    attr=msg_attr
                ))
            return result
        except Exception as e:
            logger.error(f"获取监听消息失败: {e}")
            return []

    def shutdown(self):
        """关闭监听器"""
        self._running = False
        self._executor.shutdown(wait=True)
        logger.info("MessageListener 已关闭")


class KeywordFilter:
    """
    关键词过滤器

    提供灵活的关键词匹配功能。
    """

    def __init__(self):
        self._keywords: dict[str, list[str]] = {}
        self._exact_match: dict[str, bool] = {}
        self._case_sensitive: dict[str, bool] = {}
        self._lock = threading.RLock()

    def add_pattern(
        self,
        name: str,
        keywords: list[str],
        exact_match: bool = False,
        case_sensitive: bool = False
    ):
        """
        添加关键词模式

        Args:
            name: 模式名称
            keywords: 关键词列表
            exact_match: 是否精确匹配
            case_sensitive: 是否区分大小写
        """
        with self._lock:
            self._keywords[name] = keywords
            self._exact_match[name] = exact_match
            self._case_sensitive[name] = case_sensitive

    def remove_pattern(self, name: str) -> bool:
        """
        移除关键词模式

        Args:
            name: 模式名称

        Returns:
            bool: 是否移除成功
        """
        with self._lock:
            if name in self._keywords:
                del self._keywords[name]
                del self._exact_match[name]
                del self._case_sensitive[name]
                return True
            return False

    def match(self, text: str, pattern_name: Optional[str] = None) -> bool:
        """
        匹配关键词

        Args:
            text: 待匹配文本
            pattern_name: 指定模式名称，不指定则匹配所有模式

        Returns:
            bool: 是否匹配
        """
        with self._lock:
            if pattern_name:
                return self._match_pattern(text, pattern_name)

            # 检查所有模式
            for name in self._keywords:
                if self._match_pattern(text, name):
                    return True
            return False

    def _match_pattern(self, text: str, pattern_name: str) -> bool:
        """匹配指定模式"""
        if pattern_name not in self._keywords:
            return False

        keywords = self._keywords[pattern_name]
        exact_match = self._exact_match[pattern_name]
        case_sensitive = self._case_sensitive[pattern_name]

        search_text = text if case_sensitive else text.lower()
        search_keywords = keywords if case_sensitive else [k.lower() for k in keywords]

        if exact_match:
            return search_text in search_keywords
        else:
            return any(kw in search_text for kw in search_keywords)

    def get_patterns(self) -> list[dict[str, Any]]:
        """
        获取所有模式

        Returns:
            list[Dict]: 模式列表
        """
        with self._lock:
            return [
                {
                    "name": name,
                    "keywords": self._keywords[name],
                    "exact_match": self._exact_match[name],
                    "case_sensitive": self._case_sensitive[name]
                }
                for name in self._keywords
            ]


def create_listener(wrapper) -> MessageListener:
    """
    创建监听器实例

    Args:
        wrapper: WeChatWrapper 实例

    Returns:
        MessageListener: 监听器实例
    """
    return MessageListener(wrapper)
