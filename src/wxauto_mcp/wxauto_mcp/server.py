"""
WeChat MCP Server 主入口
提供 stdio 和 HTTP/SSE 两种传输方式
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional
import platform

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.server import Server

from .rpc import MCP_SERVER
from .utils import format_result
from .singleton import MCPSingletonManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="WeChat MCP Server - 微信自动化模型上下文协议服务器"
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="传输方式: stdio (默认), http, sse"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 服务器监听地址 (默认: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP 服务器监听端口 (默认: 8000)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )

    parser.add_argument(
        "--config",
        nargs='?',
        const="mcp-configs",
        help="输出 MCP 客户端配置到指定目录 (默认: ./mcp-configs)"
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help="自动安装并配置到AI应用"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="检查 wxauto-mcp 服务器运行状态"
    )

    return parser.parse_args()


def get_claude_config_path() -> Path:
    """获取 Claude Desktop 配置文件路径"""
    config_dir = Path(os.environ.get("APPDATA", "")) / "Claude"
    return config_dir / "claude_desktop_config.json"


def get_claude_code_config_path() -> Path:
    """获取 Claude Code 配置文件路径"""
    return Path.home() / ".claude.json"


def generate_claude_config(output_path: str, transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000) -> None:
    """
    生成 Claude Desktop 配置文件

    Args:
        output_path: 输出文件路径
        transport: 传输方式
        host: 服务器地址
        port: 服务器端口
    """
    config = {
        "mcpServers": {
            "wxauto": {
                "command": sys.executable,
                "args": ["-m", "wxauto_mcp.server"],
            }
        }
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info(f"Claude 配置已生成: {output_file}")


def generate_cursor_config(output_path: str) -> None:
    """
    生成 Cursor 配置文件

    Args:
        output_path: 输出文件路径
    """
    config = {
        "mcpServers": {
            "wxauto": {
                "command": sys.executable,
                "args": ["-m", "wxauto_mcp.server"],
            }
        }
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info(f"Cursor 配置已生成: {output_file}")


def generate_all_configs(base_dir: str = "mcp-configs") -> None:
    """
    生成所有 MCP 客户端配置文件

    Args:
        base_dir: 配置文件输出目录
    """
    base_path = Path(base_dir)

    # Claude Desktop 配置
    claude_path = base_path / "claude_desktop_config.json"
    generate_claude_config(str(claude_path))

    # Cursor 配置
    cursor_path = base_path / "cursor_config.json"
    generate_cursor_config(str(cursor_path))

    # Cline (Cursor AI) 配置
    cline_path = base_path / "cline_config.json"
    generate_claude_config(str(cline_path))

    logger.info(f"[成功] 所有配置文件已生成到: {base_path.absolute()}")
    logger.info("\n[说明] 使用说明:")
    logger.info("1. Claude Desktop: 将配置内容添加到配置文件中")
    logger.info("2. Cursor: 将配置内容添加到 Cursor Settings 的 MCP 配置")


def install_to_claude() -> bool:
    """
    自动安装并配置到 Claude Desktop

    Returns:
        安装是否成功
    """
    config_path = get_claude_config_path()

    try:
        # 读取现有配置
        existing_config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)

        # 确保 mcpServers 键存在
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # 添加 wxauto MCP 服务器配置
        existing_config["mcpServers"]["wxauto"] = {
            "command": sys.executable,
            "args": ["-m", "wxauto_mcp.server"],
        }

        # 写入配置文件
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)

        logger.info(f"[成功] 已成功安装到 Claude Desktop")
        logger.info(f"[文件] 配置文件: {config_path}")
        return True

    except Exception as e:
        logger.error(f"[错误] 安装失败: {e}")
        return False


def install_to_claude_code() -> bool:
    """
    自动安装并配置到 Claude Code

    Returns:
        安装是否成功
    """
    config_path = get_claude_code_config_path()

    try:
        # 读取现有配置
        existing_config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)

        # 确保 mcpServers 键存在
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # 添加 wxauto MCP 服务器配置
        existing_config["mcpServers"]["wxauto"] = {
            "command": sys.executable,
            "args": ["-m", "wxauto_mcp.server"],
        }

        # 写入配置文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)

        logger.info(f"[成功] 已成功安装到 Claude Code")
        logger.info(f"[文件] 配置文件: {config_path}")
        return True

    except Exception as e:
        logger.error(f"[错误] 安装失败: {e}")
        return False


def install_mcp_server() -> None:
    """
    自动安装 MCP Server 到 AI 应用
    """
    logger.info("=" * 60)
    logger.info("wxauto MCP Server 自动安装")
    logger.info("=" * 60)

    # 安装到 Claude Desktop
    claude_success = install_to_claude()

    # 安装到 Claude Code
    claude_code_success = install_to_claude_code()

    if claude_success or claude_code_success:
        logger.info("\n[成功] 安装完成！")
        logger.info("\n[说明] 后续步骤:")

        if claude_success:
            logger.info("1. 重启 Claude Desktop")

        if claude_code_success:
            logger.info("2. 重启 Claude Code (如果正在使用)")

        logger.info("3. 在 Claude 中开始使用微信自动化功能")

        if claude_success:
            logger.info(f"\n[提示] Claude Desktop 配置文件: {get_claude_config_path()}")
        if claude_code_success:
            logger.info(f"[提示] Claude Code 配置文件: {get_claude_code_config_path()}")
    else:
        logger.error("\n[错误] 安装失败，请手动配置")
        logger.info("\n[说明] 手动配置:")
        logger.info("1. 运行: wxauto-mcp --config")
        logger.info("2. 将生成的配置复制到 AI 应用中")


async def start_http_server(host: str, port: int) -> None:
    """
    启动 HTTP/SSE 服务器

    Args:
        host: 监听地址
        port: 监听端口
    """
    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response
    from mcp.server.sse import SseServerTransport
    import uvicorn

    # 创建 FastAPI 应用（自带 Swagger 文档）
    app = FastAPI(
        title="WeChat MCP Server",
        description="微信自动化 MCP 服务器 - 提供 WeChat 自动化功能的 MCP 服务器",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 创建 SSE 传输层
    sse = SseServerTransport("/messages/")

    @app.get("/")
    async def root():
        """服务器信息"""
        return {
            "name": "WeChat MCP Server",
            "version": "1.0.0",
            "description": "微信自动化 MCP 服务器",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "sse": "/sse",
                "messages": "/messages/"
            }
        }

    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "healthy"}

    @app.get("/sse")
    async def handle_sse(request: Request):
        """SSE 端点 - MCP 协议通信"""
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await MCP_SERVER.run(
                streams[0], streams[1], MCP_SERVER.create_initialization_options()
            )
        # 返回空响应避免 NoneType 错误
        return Response()

    # 挂载消息处理端点到 FastAPI
    app.mount("/messages/", sse.handle_post_message)

    logger.info(f"启动 HTTP/SSE 服务器: http://{host}:{port}")
    logger.info(f"Swagger 文档: http://{host}:{port}/docs")
    logger.info(f"ReDoc 文档: http://{host}:{port}/redoc")
    logger.info(f"SSE 端点: http://{host}:{port}/sse")
    logger.info(f"消息端点: http://{host}:{port}/messages/")

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    """主入口函数"""
    args = parse_args()

    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # 自动安装
    if args.install:
        install_mcp_server()
        return

    # 生成配置文件
    if args.config:
        generate_all_configs(args.config)
        return

    # 检查状态
    if args.status:
        from .singleton import check_singleton_status
        status = check_singleton_status(args.port, args.host)
        print(status)
        return

    # 显示启动信息
    logger.info("=" * 50)
    logger.info("wxauto MCP Server 启动中...")
    logger.info(f"传输方式: {args.transport}")
    logger.info(f"Python 版本: {sys.version}")
    logger.info("=" * 50)

    # 根据传输方式启动服务器
    if args.transport == "http":
        # 单例检测：HTTP 模式
        logger.info("检查是否已有 wxauto-mcp 服务器运行...")

        singleton_check = MCPSingletonManager.ensure_singleton(args.port, args.host)

        if not singleton_check['is_new']:
            # 已有服务器运行
            logger.warning("=" * 50)
            logger.warning(f"检测到已运行的 wxauto-mcp 服务器！")
            logger.warning(f"URL: {singleton_check['url']}")
            logger.warning(f"消息: {singleton_check['message']}")
            logger.warning("=" * 50)
            logger.warning("为避免冲突，当前实例将退出")
            logger.warning("如需启动新实例，请先停止已有的服务器")
            logger.warning("=" * 50)
            logger.info("")
            logger.info("提示：多个 AI 应用可以共享同一个 wxauto-mcp 服务器")
            logger.info(f"只需在配置中都使用相同的 URL: {singleton_check['url']}")
            return

        await start_http_server(args.host, args.port)
    elif args.transport == "sse":
        # 单例检测：SSE 模式
        logger.info("检查是否已有 wxauto-mcp 服务器运行...")

        singleton_check = MCPSingletonManager.ensure_singleton(args.port, args.host)

        if not singleton_check['is_new']:
            # 已有服务器运行
            logger.warning("=" * 50)
            logger.warning(f"检测到已运行的 wxauto-mcp 服务器！")
            logger.warning(f"URL: {singleton_check['url']}")
            logger.warning(f"消息: {singleton_check['message']}")
            logger.warning("=" * 50)
            logger.warning("为避免冲突，当前实例将退出")
            logger.warning("如需启动新实例，请先停止已有的服务器")
            logger.warning("=" * 50)
            return

        await start_http_server(args.host, args.port)
    else:  # stdio
        # 使用 MCP stdio 传输
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await MCP_SERVER.run(
                read_stream,
                write_stream,
                MCP_SERVER.create_initialization_options()
            )


def main_sync() -> None:
    """同步入口函数"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}", exc_info=True)
        sys.exit(1)


def main_http() -> None:
    """HTTP 模式入口函数"""
    # 保留原始参数，只添加或覆盖 transport 参数
    new_argv = [sys.argv[0]]

    # 解析原始参数，跳过程序名
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        # 跳过已有的 transport 参数
        if arg == "--transport":
            i += 2  # 跳过参数值
            continue

        # 保留其他所有参数（包括 --port, --host, --log-level 等）
        new_argv.append(arg)
        i += 1

    # 添加 HTTP transport 参数
    new_argv.extend(["--transport", "http"])

    # 更新 sys.argv
    sys.argv = new_argv
    main_sync()


if __name__ == "__main__":
    main_sync()
