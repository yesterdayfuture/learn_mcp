"""
STDIO 模式演示客户端
通过 subprocess 启动 STDIO 服务端，通过管道通信

运行方式:
    python demo_stdio_client.py

注意: STDIO 客户端通过进程间通信与 STDIO 服务端配合使用
"""
import asyncio
import json
import subprocess
import sys


class StdioMCPClient:
    """
    STDIO 模式的 MCP 客户端
    通过 subprocess 启动服务端，通过 stdin/stdout 进行 JSON-RPC 通信
    """

    def __init__(self):
        """初始化 STDIO 客户端"""
        self._request_id = 1
        self._process = None

    async def start(self):
        """
        启动 STDIO 服务端进程
        """
        self._process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "zero_fastmcp.examples.demo_stdio_server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.sleep(0.5)

    async def _send_request(self, method: str, params: dict = None) -> dict:
        """
        发送 JSON-RPC 请求到服务端

        Args:
            method: MCP 方法名
            params: 方法参数

        Returns:
            解析后的 JSON 响应
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }
        self._request_id += 1

        request_str = json.dumps(request) + "\n"
        self._process.stdin.write(request_str.encode())
        await self._process.stdin.drain()

        response_line = await self._process.stdout.readline()
        response = json.loads(response_line.decode().strip())
        return response

    async def list_tools(self) -> dict:
        """列出所有工具"""
        return await self._send_request("tools/list")

    async def call_tool(self, name: str, arguments: dict = None) -> dict:
        """调用工具"""
        return await self._send_request("tools/call", {"name": name, "arguments": arguments or {}})

    async def list_prompts(self) -> dict:
        """列出所有提示词"""
        return await self._send_request("prompts/list")

    async def get_prompt(self, name: str, arguments: dict = None) -> dict:
        """获取提示词"""
        return await self._send_request("prompts/get", {"name": name, "arguments": arguments or {}})

    async def list_resources(self) -> dict:
        """列出所有资源"""
        return await self._send_request("resources/list")

    async def read_resource(self, uri: str) -> dict:
        """读取资源"""
        return await self._send_request("resources/read", {"uri": uri})

    async def close(self):
        """关闭客户端，终止服务端进程"""
        if self._process:
            self._process.terminate()
            await self._process.wait()


async def main():
    """主函数：演示 STDIO 客户端的各种功能"""
    client = StdioMCPClient()
    await client.start()

    print("=== 列出所有工具 ===")
    response = await client.list_tools()
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()

    print("=== 调用工具 (add) ===")
    response = await client.call_tool("add", {"a": 5, "b": 3})
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()

    print("=== 调用工具 (subtract) ===")
    response = await client.call_tool("subtract", {"a": 10, "b": 3})
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()

    print("=== 列出所有提示词 ===")
    response = await client.list_prompts()
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()

    print("=== 获取提示词 ===")
    response = await client.get_prompt("welcome", {"name": "Alice"})
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()

    print("=== 列出所有资源 ===")
    response = await client.list_resources()
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()

    print("=== 读取资源 ===")
    response = await client.read_resource("resource://config")
    print(json.dumps(response, ensure_ascii=False, indent=2))

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
