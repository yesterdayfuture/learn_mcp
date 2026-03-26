"""
STDIO 传输适配器
通过标准输入输出进行 JSON-RPC 通信
适用于命令行工具和本地进程通信
"""
import asyncio
import sys
import json
from typing import Optional
from ..server import MCPServer


class StdioTransport:
    """
    STDIO 传输类
    从标准输入读取 JSON-RPC 请求，向标准输出写入响应
    """

    def __init__(self, server: MCPServer):
        """
        初始化 STDIO 传输

        Args:
            server: MCP 服务端实例
        """
        self.server = server
        self.handler = server.get_jsonrpc_handler()
        self.running = False

    async def start(self):
        """
        启动 STDIO 传输
        持续从标准输入读取消息并处理
        """
        self.running = True
        while self.running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                response = await self.handler.handle_message(line)
                if response:
                    print(response, flush=True)
            except Exception as e:
                error_response = json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": str(e)},
                })
                print(error_response, flush=True)

    def stop(self):
        """
        停止 STDIO 传输
        """
        self.running = False


async def run_stdio(server: MCPServer):
    """
    运行 STDIO 传输的便捷函数

    Args:
        server: MCP 服务端实例

    Example:
        asyncio.run(run_stdio(server))
    """
    transport = StdioTransport(server)
    await transport.start()
