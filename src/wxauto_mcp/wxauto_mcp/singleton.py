"""
MCP 服务器单例管理器
确保全局只有一个 wxauto-mcp 服务器实例运行
"""

import socket
import psutil
import requests
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class MCPSingletonManager:
    """MCP 服务器单例管理器"""

    DEFAULT_PORT = 8181
    DEFAULT_HOST = "127.0.0.1"

    @staticmethod
    def is_port_in_use(port: int, host: str = DEFAULT_HOST) -> bool:
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                return result == 0
        except Exception:
            return False

    @staticmethod
    def is_wxauto_mcp_running(port: int = DEFAULT_PORT, host: str = DEFAULT_HOST) -> bool:
        """检查是否有 wxauto-mcp 服务器在运行"""
        if not MCPSingletonManager.is_port_in_use(port, host):
            return False

        try:
            # 尝试访问健康检查端点
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
            if response.status_code == 200:
                # 检查是否是 wxauto-mcp 服务器
                try:
                    info_response = requests.get(f"http://{host}:{port}/", timeout=2)
                    if info_response.status_code == 200:
                        data = info_response.json()
                        return data.get("name") == "WeChat MCP Server"
                except:
                    pass
        except:
            pass

        return False

    @staticmethod
    def find_wxauto_mcp_process() -> Optional[psutil.Process]:
        """查找正在运行的 wxauto-mcp 进程"""
        current_pid = psutil.Process().pid

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                # 跳过当前进程
                if proc.info['pid'] == current_pid:
                    continue

                # 检查进程命令行
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(cmdline)

                    # 检查是否是 wxauto-mcp 相关进程
                    if 'wxauto_mcp.server' in cmdline_str or 'wxauto-mcp-http' in cmdline_str:
                        return proc

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    @staticmethod
    def get_existing_server_url(port: int = DEFAULT_PORT, host: str = DEFAULT_HOST) -> Optional[str]:
        """获取已存在的服务器URL"""
        if MCPSingletonManager.is_wxauto_mcp_running(port, host):
            return f"http://{host}:{port}/sse"
        return None

    @staticmethod
    def ensure_singleton(port: int = DEFAULT_PORT, host: str = DEFAULT_HOST) -> dict:
        """
        确保单例服务器运行

        Returns:
            dict: {
                'is_new': bool,  # 是否是新启动的服务器
                'url': str,     # 服务器URL
                'message': str  # 状态消息
            }
        """
        # 检查是否已有服务器在运行
        existing_url = MCPSingletonManager.get_existing_server_url(port, host)

        if existing_url:
            logger.info(f"检测到已运行的 wxauto-mcp 服务器: {existing_url}")

            # 查找对应的进程
            proc = MCPSingletonManager.find_wxauto_mcp_process()
            if proc:
                uptime = time.time() - proc.info.get('create_time', time.time())
                logger.info(f"服务器进程 PID: {proc.info['pid']}, 运行时间: {uptime:.0f}秒")

            return {
                'is_new': False,
                'url': existing_url,
                'message': f"连接到已存在的 wxauto-mcp 服务器 ({existing_url})"
            }

        # 没有找到运行中的服务器，需要启动新的
        logger.info("未检测到运行中的 wxauto-mcp 服务器，将启动新实例")

        return {
            'is_new': True,
            'url': f"http://{host}:{port}/sse",
            'message': "将启动新的 wxauto-mcp 服务器实例"
        }


def check_singleton_status(port: int = 8181, host: str = "127.0.0.1") -> str:
    """
    检查单例状态（用于命令行工具）

    Returns:
        str: 状态报告
    """
    result = MCPSingletonManager.ensure_singleton(port, host)

    lines = [
        "=" * 60,
        "wxauto-mcp 服务器状态",
        "=" * 60,
        f"端口: {host}:{port}",
        f"状态: {'运行中' if not result['is_new'] else '未运行'}",
        f"URL: {result['url']}",
        f"消息: {result['message']}",
    ]

    if not result['is_new']:
        proc = MCPSingletonManager.find_wxauto_mcp_process()
        if proc:
            uptime = time.time() - proc.info.get('create_time', time.time())
            lines.extend([
                f"进程 PID: {proc.info['pid']}",
                f"运行时间: {uptime:.0f} 秒 ({uptime/60:.1f} 分钟)"
            ])

    lines.extend([
        "=" * 60
    ])

    return '\n'.join(lines)


if __name__ == "__main__":
    # 测试单例检测
    print(check_singleton_status())