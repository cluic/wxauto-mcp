"""
配置管理模块
支持环境变量、配置文件和默认配置
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class WeChatConfig:
    """
    微信配置

    Attributes:
        license_key: 激活密钥
        resize: 是否自动调整窗口尺寸
        debug: 是否开启调试模式
        log_level: 日志级别
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        timeout: 操作超时时间（秒）
        download_dir: 下载目录
        enable_listener: 是否启用监听器
        listener_workers: 监听器工作线程数
    """
    license_key: str = ""
    resize: bool = True
    debug: bool = False
    log_level: str = "INFO"
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    download_dir: str = "./downloads"
    enable_listener: bool = True
    listener_workers: int = 4

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "license_key": "***" if self.license_key else "",  # 隐藏密钥
            "resize": self.resize,
            "debug": self.debug,
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "download_dir": self.download_dir,
            "enable_listener": self.enable_listener,
            "listener_workers": self.listener_workers
        }


class ConfigManager:
    """
    配置管理器

    支持从环境变量、配置文件加载配置。
    """

    # 环境变量映射
    ENV_MAPPING = {
        "WECHAT_LICENSE_KEY": "license_key",
        "WECHAT_RESIZE": "resize",
        "WECHAT_DEBUG": "debug",
        "WECHAT_LOG_LEVEL": "log_level",
        "WECHAT_MAX_RETRIES": "max_retries",
        "WECHAT_RETRY_DELAY": "retry_delay",
        "WECHAT_TIMEOUT": "timeout",
        "WECHAT_DOWNLOAD_DIR": "download_dir",
        "WECHAT_ENABLE_LISTENER": "enable_listener",
        "WECHAT_LISTENER_WORKERS": "listener_workers"
    }

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            env_file: .env 文件路径
        """
        self._config: Optional[WeChatConfig] = None
        self._env_file = env_file or ".env"
        self._load_env_file()

    def _load_env_file(self):
        """加载 .env 文件"""
        if not DOTENV_AVAILABLE:
            logger.debug("python-dotenv 未安装，跳过 .env 文件加载")
            return

        env_path = Path(self._env_file)
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"已加载配置文件: {env_path}")
        else:
            logger.debug(f".env 文件不存在: {env_path}")

    def load_config(self) -> WeChatConfig:
        """
        加载配置

        Returns:
            WeChatConfig: 配置对象
        """
        if self._config is None:
            self._config = self._build_config()
        return self._config

    def _build_config(self) -> WeChatConfig:
        """构建配置对象"""
        config_dict = {}

        # 从环境变量读取
        for env_key, attr_name in self.ENV_MAPPING.items():
            value = os.getenv(env_key)
            if value is not None:
                config_dict[attr_name] = self._parse_value(env_key, value)

        # 创建配置对象
        return WeChatConfig(**config_dict)

    def _parse_value(self, env_key: str, value: str) -> Any:
        """
        解析环境变量值

        Args:
            env_key: 环境变量键
            value: 值

        Returns:
            解析后的值
        """
        # 布尔值
        if env_key in ("WECHAT_RESIZE", "WECHAT_DEBUG", "WECHAT_ENABLE_LISTENER"):
            return value.lower() in ("true", "1", "yes", "on")

        # 整数
        if env_key in ("WECHAT_MAX_RETRIES", "WECHAT_TIMEOUT", "WECHAT_LISTENER_WORKERS"):
            return int(value)

        # 浮点数
        if env_key == "WECHAT_RETRY_DELAY":
            return float(value)

        # 字符串
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        config = self.load_config()
        return getattr(config, key, default)

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键
            value: 值
        """
        config = self.load_config()
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise AttributeError(f"无效的配置键: {key}")

    def reload(self):
        """重新加载配置"""
        self._config = None
        self._load_env_file()
        logger.info("配置已重新加载")

    def save_to_env(self, path: Optional[str] = None):
        """
        保存配置到 .env 文件

        Args:
            path: 文件路径
        """
        config = self.load_config()
        env_path = Path(path or self._env_file)

        lines = []
        for env_key, attr_name in self.ENV_MAPPING.items():
            value = getattr(config, attr_name, None)
            if value is not None:
                # 隐藏密钥
                if attr_name == "license_key" and value:
                    lines.append(f"{env_key}=***")
                else:
                    lines.append(f"{env_key}={value}")

        env_path.write_text("\n".join(lines))
        logger.info(f"配置已保存到: {env_path}")

    @staticmethod
    def setup_logging(log_level: str = "INFO"):
        """
        设置日志

        Args:
            log_level: 日志级别
        """
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


# 全局配置管理器
_global_config: Optional[ConfigManager] = None


def get_config(env_file: Optional[str] = None) -> ConfigManager:
    """
    获取全局配置管理器

    Args:
        env_file: .env 文件路径

    Returns:
        ConfigManager: 配置管理器
    """
    global _global_config

    if _global_config is None or env_file:
        _global_config = ConfigManager(env_file=env_file)

    return _global_config


def load_config(env_file: Optional[str] = None) -> WeChatConfig:
    """
    快捷方式：加载配置

    Args:
        env_file: .env 文件路径

    Returns:
        WeChatConfig: 配置对象
    """
    return get_config(env_file).load_config()
