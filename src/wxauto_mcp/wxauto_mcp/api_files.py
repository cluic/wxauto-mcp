"""
文件 API 模块
提供发送文件、图片等文件相关操作
"""

import logging
from typing import Union
from pathlib import Path

from .rpc import tool
from .utils import format_result, validate_file_path

logger = logging.getLogger(__name__)

# 导入 WeChatWrapper
try:
    import sys

    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from core.wechat_wrapper import get_wechat

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
    name="send_files",
    description="发送文件。参数: filepath (文件路径，支持逗号分隔的多个文件), who (接收人，可选), exact (精确匹配，默认false)"
)
def send_files(
    filepath: str,
    who: str = None,
    exact: bool = False
) -> str:
    """
    发送文件

    Args:
        filepath: 文件路径，支持单个或逗号分隔的多个文件
        who: 接收人名称，不指定则发送给当前聊天
        exact: 是否精确匹配联系人

    Returns:
        JSON 格式的发送结果
    """
    if not filepath:
        return format_result(False, "文件路径不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        # 解析文件列表
        file_list = [f.strip() for f in filepath.split(",") if f.strip()]

        # 验证文件存在
        missing_files = [f for f in file_list if not validate_file_path(f)]
        if missing_files:
            return format_result(False, f"文件不存在: {', '.join(missing_files)}")

        result = wrapper.send_files(filepath=file_list, who=who, exact=exact)
        return format_result(result.success, result.message, result.data)
    except Exception as e:
        logger.error(f"发送文件失败: {e}")
        return format_result(False, f"发送文件失败: {e}")


@tool(
    name="send_image",
    description="发送图片。参数: filepath (图片路径), who (接收人，可选)"
)
def send_image(filepath: str, who: str = None) -> str:
    """
    发送图片

    Args:
        filepath: 图片文件路径
        who: 接收人名称，不指定则发送给当前聊天

    Returns:
        JSON 格式的发送结果
    """
    if not filepath:
        return format_result(False, "图片路径不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        # 验证文件存在
        if not validate_file_path(filepath):
            return format_result(False, f"图片文件不存在: {filepath}")

        # 验证是否为图片文件
        path = Path(filepath)
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if path.suffix.lower() not in image_extensions:
            return format_result(False, f"不支持的图片格式: {path.suffix}")

        result = wrapper.send_files(filepath=filepath, who=who)
        return format_result(result.success, result.message, result.data)
    except Exception as e:
        logger.error(f"发送图片失败: {e}")
        return format_result(False, f"发送图片失败: {e}")


@tool(
    name="send_directory_files",
    description="发送目录下的所有文件。参数: directory (目录路径), who (接收人，可选), pattern (文件匹配模式，默认*)"
)
def send_directory_files(
    directory: str,
    who: str = None,
    pattern: str = "*"
) -> str:
    """
    发送目录下的所有文件

    Args:
        directory: 目录路径
        who: 接收人名称
        pattern: 文件匹配模式 (如 *.pdf)

    Returns:
        JSON 格式的发送结果
    """
    if not directory:
        return format_result(False, "目录路径不能为空")

    wrapper = _get_wrapper()
    if not wrapper:
        return format_result(False, "微信未初始化")

    try:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return format_result(False, f"目录不存在或不是有效目录: {directory}")

        # 查找匹配的文件
        files = [str(f) for f in dir_path.glob(pattern) if f.is_file()]

        if not files:
            return format_result(False, f"目录中没有匹配 '{pattern}' 的文件")

        # 限制文件数量
        if len(files) > 10:
            return format_result(False, f"文件数量过多 ({len(files)} 个)，最多支持 10 个")

        result = wrapper.send_files(filepath=files, who=who)
        return format_result(result.success, result.message, result.data)
    except Exception as e:
        logger.error(f"发送目录文件失败: {e}")
        return format_result(False, f"发送目录文件失败: {e}")


@tool(
    name="check_file_exists",
    description="检查文件是否存在。参数: filepath (文件路径)"
)
def check_file_exists(filepath: str) -> str:
    """
    检查文件是否存在

    Args:
        filepath: 文件路径

    Returns:
        JSON 格式的检查结果
    """
    if not filepath:
        return format_result(False, "文件路径不能为空")

    try:
        path = Path(filepath)
        exists = path.exists()
        is_file = path.is_file() if exists else False
        size = path.stat().st_size if exists and is_file else None

        return format_result(
            True,
            f"文件{'存在' if exists else '不存在'}",
            {
                "exists": exists,
                "is_file": is_file,
                "size": size,
                "path": str(path.absolute())
            }
        )
    except Exception as e:
        logger.error(f"检查文件失败: {e}")
        return format_result(False, f"检查文件失败: {e}")
