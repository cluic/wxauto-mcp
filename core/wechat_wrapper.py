"""
wxautox4 WeChat 类封装
提供单例模式、激活管理、错误处理和简洁的 API 接口
"""

import os
import sys
import time
import logging
from typing import Optional, Any, Callable, Union
from functools import wraps
from threading import Lock, RLock
from pathlib import Path

# 导入 wxautox4
try:
    from wxautox4 import WeChat as WXWeChat
    from wxautox4.utils.useful import authenticate, check_license
    from wxautox4.msgs import BaseMessage
    from wxautox4 import Chat
    WXAUTO_AVAILABLE = True
except ImportError:
    WXAUTO_AVAILABLE = False
    WXWeChat = None

# 导入本地模型
from .models import (
    MessageResult, ContactInfo, SessionInfo, MessageInfo,
    WeChatStatus, ListenConfig, MessageType, MessageAttribute,
    ChatType, SendStatus
)


# 配置日志
logger = logging.getLogger(__name__)


class WeChatError(Exception):
    """微信操作异常基类"""
    pass


class ActivationError(WeChatError):
    """激活异常"""
    pass


class OfflineError(WeChatError):
    """离线异常"""
    pass


class ChatNotFoundError(WeChatError):
    """聊天窗口不存在异常"""
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 1.0,
                     exceptions: tuple = (Exception,)):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 失败，第 {attempt + 1} 次重试... 错误: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} 失败，已达最大重试次数 {max_retries}")
            raise last_error
        return wrapper
    return decorator


def require_online(func: Callable):
    """要求微信在线的装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_online():
            raise OfflineError("微信未运行或未登录")
        return func(self, *args, **kwargs)
    return wrapper


class WeChatWrapper:
    """
    wxautox4 WeChat 类的封装

    提供单例模式、激活管理、错误处理和简洁的 API 接口。

    Attributes:
        _instance: 单例实例
        _lock: 线程锁
        _wx: wxautox4 WeChat 实例
        _license_key: 激活密钥
        _is_activated: 激活状态
    """
    _instance: Optional["WeChatWrapper"] = None
    _lock = Lock()
    _wx_lock = RLock()

    def __new__(cls, license_key: Optional[str] = None):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, license_key: Optional[str] = None):
        """
        初始化 WeChat 封装

        Args:
            license_key: 激活密钥，如果不提供则从环境变量读取
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return

        if not WXAUTO_AVAILABLE:
            raise ImportError("wxautox4 未安装，请运行: pip install wxautox4")

        # 获取激活密钥
        self._license_key = license_key or os.getenv("WECHAT_LICENSE_KEY", "")
        self._is_activated = False
        self._wx: Optional[WXWeChat] = None
        self._initialized = True

        logger.info("WeChatWrapper 初始化完成")

    def check_activation(self) -> bool:
        """
        检查激活状态

        Returns:
            bool: 是否已激活
        """
        try:
            self._is_activated = check_license()
            logger.info(f"激活状态检查: {'已激活' if self._is_activated else '未激活'}")
            return self._is_activated
        except Exception as e:
            logger.error(f"检查激活状态失败: {e}")
            return False

    def activate(self, license_key: Optional[str] = None) -> MessageResult:
        """
        激活 wxautox4

        Args:
            license_key: 激活密钥，如果不提供则使用初始化时的密钥

        Returns:
            MessageResult: 激活结果
        """
        key = license_key or self._license_key
        if not key:
            return MessageResult.from_error("未提供激活密钥")

        try:
            result = authenticate(key)
            if result:
                self._is_activated = True
                self._license_key = key
                logger.info("激活成功")
                return MessageResult.from_success("激活成功")
            else:
                logger.error("激活失败: 密钥无效")
                return MessageResult.from_error("激活失败: 密钥无效", SendStatus.FAILED)
        except Exception as e:
            logger.error(f"激活异常: {e}")
            return MessageResult.from_error(f"激活异常: {e}")

    def ensure_activated(self) -> bool:
        """
        确保已激活，如果未激活则尝试激活

        Returns:
            bool: 是否激活成功
        """
        if self._is_activated or self.check_activation():
            return True

        if self._license_key:
            result = self.activate()
            return result.success

        return False

    def initialize(self, resize: bool = True, debug: bool = False) -> MessageResult:
        """
        初始化 WeChat 实例

        Args:
            resize: 是否自动调整窗口尺寸
            debug: 是否开启调试模式

        Returns:
            MessageResult: 初始化结果
        """
        try:
            # 确保已激活
            if not self.ensure_activated():
                return MessageResult.from_error(
                    "wxautox4 未激活，请设置 WECHAT_LICENSE_KEY 环境变量或调用 activate()",
                    SendStatus.FAILED
                )

            # 创建 WeChat 实例
            with self._wx_lock:
                if self._wx is None:
                    self._wx = WXWeChat(resize=resize, debug=debug)
                    logger.info("WeChat 实例创建成功")

            return MessageResult.from_success("初始化成功")

        except SystemExit as e:
            # wxautox4 未激活时会调用 sys.exit(0)
            return MessageResult.from_error(
                "wxautox4 未激活，请先调用 activate() 方法",
                SendStatus.FAILED
            )
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return MessageResult.from_error(f"初始化失败: {e}")

    @property
    def wx(self) -> WXWeChat:
        """获取底层 WeChat 实例"""
        if self._wx is None:
            raise WeChatError("WeChat 未初始化，请先调用 initialize()")
        return self._wx

    def is_online(self) -> bool:
        """
        检查微信是否在线

        Returns:
            bool: 是否在线
        """
        try:
            if self._wx is None:
                return False
            return self._wx.IsOnline()
        except Exception as e:
            logger.error(f"检查在线状态失败: {e}")
            return False

    def get_status(self) -> WeChatStatus:
        """
        获取微信状态

        Returns:
            WeChatStatus: 状态信息
        """
        try:
            if not self.is_online():
                return WeChatStatus(is_online=False, is_activated=self._is_activated)

            my_info = self.wx.GetMyInfo()
            return WeChatStatus(
                is_online=True,
                account_name=my_info.get("微信名"),
                account_id=my_info.get("微信号"),
                is_activated=self._is_activated
            )
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return WeChatStatus(is_online=False, is_activated=self._is_activated)

    @require_online
    @retry_on_failure(max_retries=2, delay=0.5)
    def chat_with(self, who: str, exact: bool = False) -> MessageResult:
        """
        切换到指定聊天窗口

        Args:
            who: 联系人名称
            exact: 是否精确匹配

        Returns:
            MessageResult: 切换结果
        """
        try:
            with self._wx_lock:
                self.wx.ChatWith(who=who, exact=exact)

                # 验证切换是否成功
                info = self.wx.ChatInfo()
                if info.get("chat_name") == who:
                    logger.info(f"成功切换到聊天: {who}")
                    return MessageResult.from_success(
                        f"切换成功",
                        data={"chat_name": who, "chat_info": info}
                    )
                else:
                    logger.warning(f"切换失败: 期望 {who}，实际 {info.get('chat_name')}")
                    return MessageResult.from_error(
                        f"切换失败: 聊天名称不匹配",
                        SendStatus.FAILED
                    )
        except Exception as e:
            logger.error(f"切换聊天失败: {e}")
            return MessageResult.from_error(f"切换聊天失败: {e}")

    @require_online
    def get_chat_info(self) -> dict[str, Any]:
        """
        获取当前聊天信息

        Returns:
            dict: 聊天信息
        """
        try:
            return self.wx.ChatInfo()
        except Exception as e:
            logger.error(f"获取聊天信息失败: {e}")
            return {}

    @require_online
    @retry_on_failure(max_retries=2, delay=0.5)
    def send_message(
        self,
        msg: str,
        who: Optional[str] = None,
        clear: bool = True,
        at: Optional[Union[str, list[str]]] = None,
        exact: bool = False
    ) -> MessageResult:
        """
        发送文本消息

        Args:
            msg: 消息内容
            who: 发送对象，不指定则发送给当前聊天
            clear: 发送后是否清空编辑框
            at: @对象，支持字符串或列表
            exact: 搜索联系人时是否精确匹配

        Returns:
            MessageResult: 发送结果
        """
        try:
            with self._wx_lock:
                response = self.wx.SendMsg(msg=msg, who=who, clear=clear, at=at, exact=exact)

                # 检查响应
                if hasattr(response, 'success') and not response.success:
                    return MessageResult.from_error(
                        response.message or "发送失败",
                        SendStatus.FAILED
                    )

                logger.info(f"消息发送成功: {msg[:50]}... -> {who or '当前聊天'}")
                return MessageResult.from_success(
                    "发送成功",
                    data={"msg": msg, "who": who}
                )
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return MessageResult.from_error(f"发送消息失败: {e}")

    @require_online
    @retry_on_failure(max_retries=2, delay=0.5)
    def send_files(
        self,
        filepath: Union[str, list[str]],
        who: Optional[str] = None,
        exact: bool = False
    ) -> MessageResult:
        """
        发送文件

        Args:
            filepath: 文件路径，支持单个或多个
            who: 发送对象
            exact: 搜索联系人时是否精确匹配

        Returns:
            MessageResult: 发送结果
        """
        try:
            # 验证文件存在
            files = filepath if isinstance(filepath, list) else [filepath]
            for f in files:
                if not Path(f).exists():
                    return MessageResult.from_error(
                        f"文件不存在: {f}",
                        SendStatus.FAILED
                    )

            with self._wx_lock:
                response = self.wx.SendFiles(filepath=filepath, who=who, exact=exact)

                if hasattr(response, 'success') and not response.success:
                    return MessageResult.from_error(
                        response.message or "发送失败",
                        SendStatus.FAILED
                    )

                logger.info(f"文件发送成功: {len(files)} 个文件 -> {who or '当前聊天'}")
                return MessageResult.from_success(
                    f"发送成功: {len(files)} 个文件",
                    data={"file_count": len(files), "who": who}
                )
        except Exception as e:
            logger.error(f"发送文件失败: {e}")
            return MessageResult.from_error(f"发送文件失败: {e}")

    @require_online
    def get_sessions(self) -> list[SessionInfo]:
        """
        获取会话列表

        Returns:
            list[SessionInfo]: 会话信息列表
        """
        try:
            sessions = self.wx.GetSession()
            result = []
            for session in sessions:
                info = session.info
                result.append(SessionInfo(
                    name=info.get("name", ""),
                    time=info.get("time"),
                    content=info.get("content"),
                    isnew=info.get("isnew", False),
                    new_count=info.get("new_count", 0),
                    ismute=info.get("ismute", False)
                ))
            return result
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    @require_online
    def get_all_messages(self) -> list[MessageInfo]:
        """
        获取当前聊天窗口所有消息

        Returns:
            list[MessageInfo]: 消息列表
        """
        try:
            messages = self.wx.GetAllMessage()
            result = []
            for msg in messages:
                result.append(MessageInfo(
                    content=msg.content,
                    sender=msg.sender,
                    msg_type=MessageType(msg.type) if msg.type in MessageType.__members__ else MessageType.TEXT,
                    attr=MessageAttribute(msg.attr) if msg.attr in MessageAttribute.__members__ else MessageAttribute.FRIEND,
                    chat_name=msg.chat.get("name") if hasattr(msg, 'chat') else None
                ))
            return result
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return []

    @require_online
    def get_history_messages(self, n: int = 50) -> list[MessageInfo]:
        """
        获取历史消息

        Args:
            n: 最大获取消息数量

        Returns:
            list[MessageInfo]: 消息列表
        """
        try:
            messages = self.wx.GetHistoryMessage(n=n)
            result = []
            for msg in messages:
                result.append(MessageInfo(
                    content=msg.content,
                    sender=msg.sender,
                    msg_type=MessageType(msg.type) if msg.type in MessageType.__members__ else MessageType.TEXT,
                    attr=MessageAttribute(msg.attr) if msg.attr in MessageAttribute.__members__ else MessageAttribute.FRIEND
                ))
            return result
        except Exception as e:
            logger.error(f"获取历史消息失败: {e}")
            return []

    @require_online
    def get_recent_groups(self) -> list[str]:
        """
        获取最近群聊列表

        Returns:
            list[str]: 群聊名称列表
        """
        try:
            groups = self.wx.GetAllRecentGroups()
            if isinstance(groups, list):
                return groups
            return []
        except Exception as e:
            logger.error(f"获取群聊列表失败: {e}")
            return []

    @require_online
    def get_friend_details(
        self,
        n: int = 10,
        save_head_image: bool = False
    ) -> list[ContactInfo]:
        """
        获取好友列表

        Args:
            n: 获取数量
            save_head_image: 是否获取头像

        Returns:
            list[ContactInfo]: 好友信息列表
        """
        try:
            friends = self.wx.GetFriendDetails(
                n=n,
                timeout=0xFFFFF,
                save_head_image=save_head_image,
                save_head_wait=0
            )
            result = []
            for friend in friends:
                result.append(ContactInfo(
                    name=friend.get("昵称", ""),
                    alias=friend.get("微信号"),
                    remark=friend.get("标签"),
                    avatar=friend.get("头像"),
                    signature=friend.get("个性签名"),
                    source=friend.get("来源"),
                    mutual_groups=friend.get("共同群聊")
                ))
            return result
        except Exception as e:
            logger.error(f"获取好友列表失败: {e}")
            return []

    @require_online
    def get_sub_window(self, nickname: str):
        """
        获取子窗口实例

        Args:
            nickname: 联系人名称

        Returns:
            Chat: 子窗口对象，如果不存在返回 None
        """
        try:
            return self.wx.GetSubWindow(nickname=nickname)
        except Exception as e:
            logger.error(f"获取子窗口失败: {e}")
            return None

    @require_online
    def get_all_sub_windows(self) -> list[Any]:
        """
        获取所有子窗口

        Returns:
            list[Chat]: 子窗口列表
        """
        try:
            return self.wx.GetAllSubWindow() or []
        except Exception as e:
            logger.error(f"获取子窗口列表失败: {e}")
            return []

    def keep_running(self):
        """
        保持程序运行（监听模式必需）

        此方法会阻塞主线程，用于消息监听场景。
        """
        if self._wx is None:
            logger.error("WeChat 未初始化")
            return

        logger.info("进入监听模式，按 Ctrl+C 退出...")
        try:
            self.wx.KeepRunning()
        except KeyboardInterrupt:
            logger.info("退出监听模式")


# 创建全局实例
_global_wrapper: Optional[WeChatWrapper] = None
_global_lock = Lock()


def get_wechat(license_key: Optional[str] = None,
               resize: bool = True,
               debug: bool = False) -> WeChatWrapper:
    """
    获取全局 WeChatWrapper 实例

    Args:
        license_key: 激活密钥
        resize: 是否自动调整窗口尺寸
        debug: 是否开启调试模式

    Returns:
        WeChatWrapper: 全局单例实例
    """
    global _global_wrapper

    if _global_wrapper is None:
        with _global_lock:
            if _global_wrapper is None:
                _global_wrapper = WeChatWrapper(license_key=license_key)
                _global_wrapper.initialize(resize=resize, debug=debug)

    return _global_wrapper


def reset_global_wrapper():
    """重置全局实例（用于测试）"""
    global _global_wrapper
    _global_wrapper = None
