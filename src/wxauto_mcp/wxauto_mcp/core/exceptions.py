"""
异常定义模块
定义微信自动化相关的所有异常类型
"""


class WeChatError(Exception):
    """微信操作异常基类"""
    pass


class ActivationError(WeChatError):
    """激活异常"""

    def __init__(self, message: str = "激活失败，请检查激活密钥"):
        self.message = message
        super().__init__(self.message)


class OfflineError(WeChatError):
    """离线异常"""

    def __init__(self, message: str = "微信未运行或未登录"):
        self.message = message
        super().__init__(self.message)


class ChatNotFoundError(WeChatError):
    """聊天窗口不存在异常"""

    def __init__(self, who: str = ""):
        self.who = who
        message = f"聊天窗口不存在: {who}" if who else "聊天窗口不存在"
        super().__init__(message)


class MessageSendError(WeChatError):
    """消息发送异常"""

    def __init__(self, message: str = "消息发送失败"):
        self.message = message
        super().__init__(self.message)


class ListenerError(WeChatError):
    """监听器异常"""

    def __init__(self, message: str = "监听器操作失败"):
        self.message = message
        super().__init__(self.message)


class ConfigError(WeChatError):
    """配置异常"""

    def __init__(self, message: str = "配置错误"):
        self.message = message
        super().__init__(self.message)


class FileNotFoundError(WeChatError):
    """文件不存在异常"""

    def __init__(self, filepath: str = ""):
        self.filepath = filepath
        message = f"文件不存在: {filepath}" if filepath else "文件不存在"
        super().__init__(message)


class TimeoutError(WeChatError):
    """超时异常"""

    def __init__(self, message: str = "操作超时"):
        self.message = message
        super().__init__(self.message)


__all__ = [
    "WeChatError",
    "ActivationError",
    "OfflineError",
    "ChatNotFoundError",
    "MessageSendError",
    "ListenerError",
    "ConfigError",
    "FileNotFoundError",
    "TimeoutError"
]
