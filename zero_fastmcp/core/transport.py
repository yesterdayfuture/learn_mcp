"""
传输层模块
定义传输基类和 JSON-RPC 消息处理器
"""
import json
import asyncio
from typing import Optional, Callable, Awaitable


class Transport:
    """
    传输基类
    子类需要实现 start 和 stop 方法
    """
    async def start(self, handler: Callable):
        """启动传输"""
        raise NotImplementedError

    async def stop(self):
        """停止传输"""
        raise NotImplementedError


class JSONRPCHandler:
    """
    JSON-RPC 消息处理器
    负责解析 JSON-RPC 请求并返回响应
    """

    def __init__(self, protocol_handler):
        """
        初始化 JSON-RPC 处理器

        Args:
            protocol_handler: 协议处理器实例
        """
        self.protocol_handler = protocol_handler

    async def handle_message(self, message: str) -> str:
        """
        处理 JSON-RPC 消息

        Args:
            message: JSON-RPC 格式的字符串消息

        Returns:
            JSON-RPC 格式的响应字符串
        """
        from .types import MCPRequest

        try:
            data = json.loads(message)
            request = MCPRequest(**data)
            response = await self.protocol_handler.handle_request(request)
            return response.model_dump_json(exclude_none=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
            }
            return json.dumps(error_response)
