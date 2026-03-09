"""
微信自动化核心模块

提供 wxautox4 的封装、监听器和配置管理功能。
"""

from .wechat_wrapper import (
    WeChatWrapper,
    get_wechat,
    reset_global_wrapper,
    retry_on_failure,
    require_online
)

from .exceptions import (
    WeChatError,
    ActivationError,
    OfflineError,
    ChatNotFoundError,
    MessageSendError,
    ListenerError,
    ConfigError
)

from .config import (
    ConfigManager,
    get_config,
    load_config
)

from .models import (
    MessageResult,
    ContactInfo,
    SessionInfo,
    MessageInfo,
    ListenConfig,
    WeChatStatus,
    MessageType,
    MessageAttribute,
    ChatType,
    SendStatus
)

from .listener import (
    MessageListener,
    KeywordFilter,
    CallbackPriority,
    create_listener
)

__all__ = [
    # Wrapper
    "WeChatWrapper",
    "get_wechat",
    "reset_global_wrapper",
    "retry_on_failure",
    "require_online",

    # Exceptions
    "WeChatError",
    "ActivationError",
    "OfflineError",
    "ChatNotFoundError",
    "MessageSendError",
    "ListenerError",
    "ConfigError",

    # Config
    "ConfigManager",
    "get_config",
    "load_config",

    # Models
    "MessageResult",
    "ContactInfo",
    "SessionInfo",
    "MessageInfo",
    "ListenConfig",
    "WeChatStatus",
    "MessageType",
    "MessageAttribute",
    "ChatType",
    "SendStatus",

    # Listener
    "MessageListener",
    "KeywordFilter",
    "CallbackPriority",
    "create_listener"
]

__version__ = "0.1.0"
