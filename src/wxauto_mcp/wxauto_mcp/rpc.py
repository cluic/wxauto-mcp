"""
MCP RPC 核心基础设施
提供工具注册、资源管理和输出限制系统
"""

import logging
from typing import Any, Callable, Optional
from functools import wraps
import inspect
from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)

# 输出限制（基于 ida-pro-mcp 的设计）
MAX_OUTPUT_SIZE = 50000

# 创建 MCP 服务器实例
MCP_SERVER = Server("wxauto-mcp-server")

# 不安全操作集合（用于标记需要用户确认的操作）
MCP_UNSAFE: set[str] = set()


def limit_output(func: Callable) -> Callable:
    """
    输出限制装饰器

    限制工具输出的最大长度，防止返回过大的数据。

    Args:
        func: 被装饰的函数

    Returns:
        包装后的函数
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        result = func(*args, **kwargs)
        if isinstance(result, str) and len(result) > MAX_OUTPUT_SIZE:
            logger.warning(
                f"{func.__name__} 输出超过限制 ({len(result)} > {MAX_OUTPUT_SIZE})，已截断"
            )
            return result[:MAX_OUTPUT_SIZE] + f"\n... (输出已截断，原始大小: {len(result)} 字符)"
        return result

    return wrapper


def tool(name: Optional[str] = None, description: Optional[str] = None) -> Callable:
    """
    工具装饰器

    注册函数为 MCP 工具，自动应用输出限制。

    Args:
        name: 工具名称，默认使用函数名
        description: 工具描述

    Returns:
        装饰后的函数
    """

    def decorator(func: Callable) -> Callable:
        # 应用输出限制
        limited_func = limit_output(func)

        # 注册到工具注册表
        tool_name = name or func.__name__
        TOOL_REGISTRY.register(
            name=tool_name,
            func=limited_func,
            description=description or func.__doc__ or "",
        )

        # 返回原函数，不修改其行为
        return func

    return decorator


def resource(uri: str, name: Optional[str] = None, description: Optional[str] = None) -> Callable:
    """
    资源装饰器

    注册函数为 MCP 资源。

    Args:
        uri: 资源 URI
        name: 资源名称
        description: 资源描述

    Returns:
        装饰后的函数
    """

    def decorator(func: Callable) -> Callable:
        # 注册到资源注册表
        RESOURCE_REGISTRY.register(
            uri=uri,
            func=func,
            name=name,
            description=description,
        )

        # 返回原函数，不修改其行为
        return func

    return decorator


def unsafe(func: Callable) -> Callable:
    """
    不安全操作装饰器

    标记函数为不安全操作，需要在客户端进行确认。

    Args:
        func: 被标记的函数

    Returns:
        原函数（已添加到不安全集合）
    """
    MCP_UNSAFE.add(func.__name__)
    return func


def get_unsafe_tools() -> set[str]:
    """获取所有不安全工具名称集合"""
    return MCP_UNSAFE.copy()


class ToolRegistry:
    """
    工具注册表

    管理所有已注册的 MCP 工具，提供扩展分组功能。
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self._groups: dict[str, list[str]] = {}

    def register(
        self,
        name: str,
        func: Callable,
        group: str = "default",
        description: Optional[str] = None,
        unsafe: bool = False,
    ) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            func: 工具函数
            group: 扩展分组
            description: 工具描述
            unsafe: 是否为不安全操作
        """
        self._tools[name] = {
            "func": func,
            "group": group,
            "description": description,
            "unsafe": unsafe,
        }

        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(name)

        logger.debug(f"已注册工具: {name} (分组: {group}, 不安全: {unsafe})")

    def get_tool(self, name: str) -> Optional[dict[str, Any]]:
        """获取指定工具"""
        return self._tools.get(name)

    def get_group(self, group: str) -> list[str]:
        """获取指定分组的所有工具名称"""
        return self._groups.get(group, [])

    def get_all_tools(self) -> dict[str, dict[str, Any]]:
        """获取所有工具"""
        return self._tools.copy()

    def get_all_groups(self) -> dict[str, list[str]]:
        """获取所有分组"""
        return self._groups.copy()

    def is_unsafe(self, name: str) -> bool:
        """检查工具是否为不安全操作"""
        tool_info = self._tools.get(name)
        return tool_info.get("unsafe", False) if tool_info else False


class ResourceRegistry:
    """
    资源注册表

    管理所有已注册的 MCP 资源。
    """

    def __init__(self) -> None:
        self._resources: dict[str, dict[str, Any]] = {}

    def register(
        self,
        uri: str,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        注册资源

        Args:
            uri: 资源 URI
            func: 资源函数
            name: 资源名称
            description: 资源描述
        """
        self._resources[uri] = {
            "func": func,
            "name": name,
            "description": description,
        }

        logger.debug(f"已注册资源: {uri}")

    def get_resource(self, uri: str) -> Optional[dict[str, Any]]:
        """获取指定资源"""
        return self._resources.get(uri)

    def get_all_resources(self) -> dict[str, dict[str, Any]]:
        """获取所有资源"""
        return self._resources.copy()


# 全局工具注册表实例
TOOL_REGISTRY = ToolRegistry()

# 全局资源注册表实例
RESOURCE_REGISTRY = ResourceRegistry()


# MCP 协议处理器
@MCP_SERVER.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    处理 list_tools 请求

    返回所有已注册的工具列表。
    """
    tools = []

    for name, tool_info in TOOL_REGISTRY.get_all_tools().items():
        # 获取函数签名以推断参数
        func = tool_info["func"]
        sig = inspect.signature(func)

        # 构建输入模式
        input_schema = {
            "type": "object",
            "properties": {},
        }

        if sig.parameters:
            required = []
            for param_name, param in sig.parameters.items():
                param_type = "string"

                # 简单的类型推断
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == str:
                    param_type = "string"

                input_schema["properties"][param_name] = {
                    "type": param_type,
                }

                # 检查是否有默认值
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
                else:
                    input_schema["properties"][param_name]["default"] = param.default

            if required:
                input_schema["required"] = required

        tools.append(
            Tool(
                name=name,
                description=tool_info.get("description", ""),
                inputSchema=input_schema,
            )
        )

    logger.info(f"返回工具列表: {len(tools)} 个工具")
    return tools


@MCP_SERVER.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    处理 call_tool 请求

    调用指定的工具函数并返回结果。
    """
    logger.info(f"[MCP] 调用工具: {name} 参数: {arguments}")

    tool_info = TOOL_REGISTRY.get_tool(name)
    if not tool_info:
        logger.error(f"[MCP] 未知工具: {name}")
        raise ValueError(f"未知工具: {name}")

    func = tool_info["func"]

    try:
        logger.info(f"[MCP] 执行工具函数: {name}")
        # 调用工具函数
        result = func(**arguments)

        logger.info(f"[MCP] 工具执行完成: {name}, 结果长度: {len(str(result))}")

        # 确保结果是字符串
        if not isinstance(result, str):
            result = str(result)

        logger.info(f"[MCP] 返回结果: {name}")
        return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.error(f"[MCP] 工具调用失败: {name} 错误: {e}", exc_info=True)
        raise


@MCP_SERVER.list_resources()
async def handle_list_resources() -> list[dict[str, Any]]:
    """
    处理 list_resources 请求

    返回所有已注册的资源列表。
    """
    resources = []

    for uri, resource_info in RESOURCE_REGISTRY.get_all_resources().items():
        resources.append({
            "uri": uri,
            "name": resource_info.get("name", uri),
            "description": resource_info.get("description", ""),
            "mime_type": "text/plain",
        })

    logger.info(f"返回资源列表: {len(resources)} 个资源")
    return resources


@MCP_SERVER.read_resource()
async def handle_read_resource(uri: str) -> str:
    """
    处理 read_resource 请求

    读取并返回指定资源的内容。
    """
    logger.info(f"读取资源: {uri}")

    resource_info = RESOURCE_REGISTRY.get_resource(uri)
    if not resource_info:
        raise ValueError(f"未知资源: {uri}")

    func = resource_info["func"]

    try:
        result = func()

        # 确保结果是字符串
        if not isinstance(result, str):
            result = str(result)

        return result

    except Exception as e:
        logger.error(f"资源读取失败: {uri} 错误: {e}")
        raise
