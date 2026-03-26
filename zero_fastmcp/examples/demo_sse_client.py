"""
SSE 模式演示客户端
通过 SSE 连接接收服务端推送的事件
同时通过 HTTP POST 发送请求
"""
import asyncio
import httpx
import sseclient
import json


class SSEMCPClient:
    """
    SSE 模式的 MCP 客户端
    通过 SSE 接收服务端事件，通过 HTTP 发送请求
    """

    def __init__(self, base_url: str):
        """
        初始化 SSE 客户端

        Args:
            base_url: 服务端基础 URL
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient()
        self._response_queue = asyncio.Queue()
        self._sse_task = None

    async def _handle_sse(self, response):
        """
        处理 SSE 事件流

        Args:
            response: SSE 响应对象
        """
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data:
                await self._response_queue.put(event.data)

    async def _start_sse_listener(self):
        """
        启动 SSE 监听器，在后台接收服务端推送的事件
        """
        async with self._client.stream("GET", f"{self.base_url}/sse") as response:
            await self._handle_sse(response)

    async def start(self):
        """
        启动 SSE 客户端，建立 SSE 连接并开始监听事件
        """
        self._sse_task = asyncio.create_task(self._start_sse_listener())

    async def _post(self, method: str, params: dict = None):
        """
        发送 JSON-RPC POST 请求

        Args:
            method: MCP 方法名
            params: 方法参数

        Returns:
            解析后的 JSON 响应
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        response = await self._client.post(
            f"{self.base_url}/message",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        return response.json()

    async def list_tools(self):
        """列出所有工具"""
        return await self._post("tools/list")

    async def call_tool(self, name: str, arguments: dict = None):
        """调用工具"""
        return await self._post("tools/call", {"name": name, "arguments": arguments or {}})

    async def list_prompts(self):
        """列出所有提示词"""
        return await self._post("prompts/list")

    async def get_prompt(self, name: str, arguments: dict = None):
        """获取提示词"""
        return await self._post("prompts/get", {"name": name, "arguments": arguments or {}})

    async def list_resources(self):
        """列出所有资源"""
        return await self._post("resources/list")

    async def read_resource(self, uri: str):
        """读取资源"""
        return await self._post("resources/read", {"uri": uri})

    async def close(self):
        """关闭客户端"""
        if self._sse_task:
            self._sse_task.cancel()
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def main():
    """主函数：演示 SSE 客户端的各种功能"""
    client = SSEMCPClient("http://localhost:8000")
    await client.start()

    await asyncio.sleep(0.5)

    print("=== 列出所有工具 ===")
    response = await client.list_tools()
    print(f"响应: {response}")
    print()

    print("=== 调用工具 (add) ===")
    response = await client.call_tool("add", {"a": 5, "b": 3})
    print(f"响应: {response}")
    print()

    print("=== 调用工具 (multiply) ===")
    response = await client.call_tool("multiply", {"a": 4, "b": 7})
    print(f"响应: {response}")
    print()

    print("=== 列出所有提示词 ===")
    response = await client.list_prompts()
    print(f"响应: {response}")
    print()

    print("=== 获取提示词 ===")
    response = await client.get_prompt("greeting", {"name": "Alice"})
    print(f"响应: {response}")
    print()

    print("=== 列出所有资源 ===")
    response = await client.list_resources()
    print(f"响应: {response}")
    print()

    print("=== 读取资源 ===")
    response = await client.read_resource("resource://info")
    print(f"响应: {response}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
