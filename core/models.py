"""
数据模型定义
定义微信自动化相关的数据结构
"""

from typing import Optional, , , Any, Literal
from dataclasses import dataclass, field
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    VOICE = "voice"


class MessageAttribute(str, Enum):
    """消息属性枚举"""
    SYSTEM = "system"
    SELF = "self"
    FRIEND = "friend"


class ChatType(str, Enum):
    """聊天类型枚举"""
    FRIEND = "friend"
    GROUP = "group"
    SERVICE = "service"
    OFFICIAL = "official"


class SendStatus(str, Enum):
    """发送状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class MessageResult:
    """
    消息发送结果模型

    Attributes:
        success: 是否成功
        status: 发送状态
        message: 结果消息
        error: 错误信息（如果有）
        data: 附加数据
    """
    success: bool
    status: SendStatus
    message: str = ""
    error: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "status": self.status.value,
            "message": self.message,
            "error": self.error,
            "data": self.data
        }

    @classmethod
    def from_success(cls, message: str = "操作成功", data: Optional[dict[str, Any]] = None) -> "MessageResult":
        """创建成功结果"""
        return cls(
            success=True,
            status=SendStatus.SUCCESS,
            message=message,
            data=data or {}
        )

    @classmethod
    def from_error(cls, error: str, status: SendStatus = SendStatus.ERROR) -> "MessageResult":
        """创建错误结果"""
        return cls(
            success=False,
            status=status,
            message="操作失败",
            error=error
        )


@dataclass
class ContactInfo:
    """
    联系人信息模型

    Attributes:
        name: 昵称
        alias: 微信号
        remark: 备注名
        chat_type: 聊天类型
        tags: 标签列表
        avatar: 头像路径
        signature: 个性签名
        source: 来源
        mutual_groups: 共同群聊数
    """
    name: str
    alias: Optional[str] = None
    remark: Optional[str] = None
    chat_type: ChatType = ChatType.FRIEND
    tags: list[str] = field(default_factory=list)
    avatar: Optional[str] = None
    signature: Optional[str] = None
    source: Optional[str] = None
    mutual_groups: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "alias": self.alias,
            "remark": self.remark,
            "chat_type": self.chat_type.value if isinstance(self.chat_type, ChatType) else self.chat_type,
            "tags": self.tags,
            "avatar": self.avatar,
            "signature": self.signature,
            "source": self.source,
            "mutual_groups": self.mutual_groups
        }

    @property
    def display_name(self) -> str:
        """获取显示名称（优先使用备注）"""
        return self.remark or self.name


@dataclass
class SessionInfo:
    """
    会话信息模型

    Attributes:
        name: 聊天名称
        time: 最后消息时间
        content: 最后一条消息内容
        isnew: 是否是新会话
        new_count: 未读消息数
        ismute: 是否免打扰
    """
    name: str
    time: Optional[str] = None
    content: Optional[str] = None
    isnew: bool = False
    new_count: int = 0
    ismute: bool = False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "time": self.time,
            "content": self.content,
            "isnew": self.isnew,
            "new_count": self.new_count,
            "ismute": self.ismute
        }


@dataclass
class MessageInfo:
    """
    消息信息模型

    Attributes:
        content: 消息内容
        sender: 发送者
        msg_type: 消息类型
        attr: 消息属性
        timestamp: 时间戳
        chat_name: 所属聊天名称
    """
    content: str
    sender: str
    msg_type: MessageType
    attr: MessageAttribute
    timestamp: Optional[float] = None
    chat_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "sender": self.sender,
            "type": self.msg_type.value if isinstance(self.msg_type, MessageType) else self.msg_type,
            "attr": self.attr.value if isinstance(self.attr, MessageAttribute) else self.attr,
            "timestamp": self.timestamp,
            "chat_name": self.chat_name
        }


@dataclass
class ListenConfig:
    """
    监听配置模型

    Attributes:
        nickname: 监听的联系人名称
        keywords: 关键词过滤列表
        msg_types: 消息类型过滤列表
        enabled: 是否启用
    """
    nickname: str
    keywords: list[str] = field(default_factory=list)
    msg_types: list[MessageType] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "nickname": self.nickname,
            "keywords": self.keywords,
            "msg_types": [t.value if isinstance(t, MessageType) else t for t in self.msg_types],
            "enabled": self.enabled
        }


@dataclass
class WeChatStatus:
    """
    微信状态模型

    Attributes:
        is_online: 是否在线
        account_name: 账号名称
        account_id: 微信号
        is_activated: 是否已激活
    """
    is_online: bool
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    is_activated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "is_online": self.is_online,
            "account_name": self.account_name,
            "account_id": self.account_id,
            "is_activated": self.is_activated
        }
