"""
MCP 客户端模块
提供连接 MCP 服务端并调用工具、提示词、资源的方法
"""
import httpx
import json
from typing import Optional, Dict, Any, List


class MCPClient:
    """
    MCP 客户端
    通过 HTTP 与 MCP 服务端通信
    支持工具调用、提示词获取、资源读取等功能
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        初始化 MCP 客户端

        Args:
            base_url: 服务端基础 URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def _post(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送 JSON-RPC POST 请求

        Args:
            method: MCP 方法名
            params: 方法参数

        Returns:
            解析后的 JSON 响应

        Raises:
            httpx.HTTPStatusError: HTTP 请求失败时抛出
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        response = await self._client.post(
            f"{self.base_url}/mcp",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有可用工具列表

        Returns:
            工具列表，每项包含 name、description、input_schema

        Example:
            tools = await client.list_tools()
            for tool in tools:
                print(f"Tool: {tool['name']}")
        """
        result = await self._post("tools/list")
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        调用指定工具

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果，通常是 content 列表

        Example:
            result = await client.call_tool("add", {"a": 5, "b": 3})
        """
        result = await self._post("tools/call", {"name": name, "arguments": arguments or {}})
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {}).get("content", [])

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        获取所有可用提示词列表

        Returns:
            提示词列表，每项包含 name、description、arguments

        Example:
            prompts = await client.list_prompts()
        """
        result = await self._post("prompts/list")
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {}).get("prompts", [])

    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取指定提示词

        Args:
            name: 提示词名称
            arguments: 提示词参数

        Returns:
            提示词消息列表

        Example:
            messages = await client.get_prompt("greeting", {"name": "Alice"})
        """
        result = await self._post("prompts/get", {"name": name, "arguments": arguments or {}})
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {}).get("messages", [])

    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        获取所有可用资源列表

        Returns:
            资源列表，每项包含 uri、name、description、mime_type

        Example:
            resources = await client.list_resources()
        """
        result = await self._post("resources/list")
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {}).get("resources", [])

    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """
        读取指定资源

        Args:
            uri: 资源 URI

        Returns:
            资源内容列表

        Example:
            contents = await client.read_resource("resource://config")
        """
        result = await self._post("resources/read", {"uri": uri})
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {}).get("contents", [])

    async def register_tool(self, name: str, description: str = "", input_schema: Optional[Dict[str, Any]] = None, code: str = "") -> Dict[str, Any]:
        """
        远程注册工具（支持自定义代码）

        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入参数模式
            code: Python 代码字符串，执行后返回结果

        Returns:
            注册结果

        Example:
            result = await client.register_tool(
                name="my_tool",
                description="我的工具",
                input_schema={"x": {"type": "number"}, "y": {"type": "number"}},
                code="return x + y"
            )
        """
        result = await self._post("tools/register", {
            "name": name,
            "description": description,
            "input_schema": input_schema or {},
            "code": code,
        })
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {})

    async def register_prompt(self, name: str, description: str = "", arguments: Optional[List[Dict[str, Any]]] = None, code: str = "") -> Dict[str, Any]:
        """
        远程注册提示词（支持自定义代码）

        Args:
            name: 提示词名称
            description: 提示词描述
            arguments: 参数列表
            code: Python 代码字符串，执行后返回消息列表

        Returns:
            注册结果

        Example:
            result = await client.register_prompt(
                name="greeting",
                description="问候提示词",
                arguments=[{"name": "name", "description": "姓名"}],
                code="return [{\"role\": \"user\", \"content\": f\"你好，{name}！\"}]"
            )
        """
        result = await self._post("prompts/register", {
            "name": name,
            "description": description,
            "arguments": arguments or [],
            "code": code,
        })
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {})

    async def register_resource(self, uri: str, name: str = "", description: str = "", mime_type: Optional[str] = None, code: str = "") -> Dict[str, Any]:
        """
        远程注册资源（支持自定义代码）

        Args:
            uri: 资源 URI
            name: 资源名称
            description: 资源描述
            mime_type: MIME 类型
            code: Python 代码字符串，执行后返回资源内容

        Returns:
            注册结果

        Example:
            result = await client.register_resource(
                uri="resource://my_data",
                name="my_data",
                description="我的数据",
                mime_type="application/json",
                code="return {\"key\": \"value\"}"
            )
        """
        result = await self._post("resources/register", {
            "uri": uri,
            "name": name,
            "description": description,
            "mime_type": mime_type,
            "code": code,
        })
        if "error" in result:
            raise Exception(result["error"]["message"])
        return result.get("result", {})

    async def close(self):
        """
        关闭客户端连接
        """
        await self._client.aclose()

    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器退出，自动关闭连接
        """
        await self.close()
