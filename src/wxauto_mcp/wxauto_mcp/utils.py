"""
工具函数模块
提供类型转换、格式化等辅助功能
"""

import json
import logging
from typing import Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


def format_result(success: bool, message: str, data: Optional[dict[str, Any]] = None) -> str:
    """
    格式化操作结果为 JSON 字符串

    Args:
        success: 操作是否成功
        message: 结果消息
        data: 附加数据

    Returns:
        JSON 格式的结果字符串
    """
    result = {
        "success": success,
        "message": message,
        "data": data or {},
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def format_list(items: list[Any], title: str = "结果") -> str:
    """
    格式化列表数据为可读字符串

    Args:
        items: 列表项
        title: 列表标题

    Returns:
        格式化的字符串
    """
    if not items:
        return f"{title}: 无数据"

    lines = [f"{title} (共 {len(items)} 项):"]
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            lines.append(f"  {i}. {json.dumps(item, ensure_ascii=False)}")
        else:
            lines.append(f"  {i}. {item}")
    return "\n".join(lines)


def validate_file_path(file_path: str) -> bool:
    """
    验证文件路径是否存在

    Args:
        file_path: 文件路径

    Returns:
        文件是否存在
    """
    return Path(file_path).exists()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_repr(obj: Any, max_length: int = 200) -> str:
    """
    安全的对象字符串表示

    Args:
        obj: 任意对象
        max_length: 最大长度

    Returns:
        对象的字符串表示
    """
    try:
        repr_str = repr(obj)
        return truncate_text(repr_str, max_length)
    except Exception as e:
        return f"<repr() 失败: {e}>"


def parse_contacts(contacts_str: str) -> list[str]:
    """
    解析联系人字符串

    支持多种格式：
    - 单个名称: "张三"
    - 逗号分隔: "张三,李四,王五"
    - 换行分隔: "张三\n李四\n王五"

    Args:
        contacts_str: 联系人字符串

    Returns:
        联系人名称列表
    """
    if not contacts_str:
        return []

    # 尝试 JSON 解析
    try:
        data = json.loads(contacts_str)
        if isinstance(data, list):
            return [str(item) for item in data]
        elif isinstance(data, str):
            contacts_str = data
    except json.JSONDecodeError:
        pass

    # 按逗号或换行分割
    contacts = []
    for line in contacts_str.replace(",", "\n").split("\n"):
        line = line.strip()
        if line:
            contacts.append(line)

    return contacts


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    """
    合并多个字典

    Args:
        *dicts: 要合并的字典

    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def get_nested_value(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    获取嵌套字典中的值

    Args:
        data: 字典数据
        *keys: 键路径
        default: 默认值

    Returns:
        找到的值或默认值
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default
