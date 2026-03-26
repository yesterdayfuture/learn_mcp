"""
MCP 服务端核心模块
提供工具、提示词、资源的注册功能
支持装饰器和手动添加两种注册方式
"""
from typing import Dict, Callable, Optional, List, Any
from ..core.protocol import ProtocolHandler
from ..core.transport import JSONRPCHandler
from .stats import get_stats, ServerStats
import json


class MCPServer:
    """
    MCP 服务端
    负责注册和管理工具、提示词、资源
    支持中间件处理请求
    """

    def __init__(
        self,
        name: str = "mcp-server",
        version: str = "1.0.0",
        middleware: Optional[List[Callable]] = None,
        stats: Optional[ServerStats] = None,
    ):
        """
        初始化 MCP 服务端

        Args:
            name: 服务端名称
            version: 服务端版本
            middleware: 中间件列表，按顺序执行
            stats: 统计管理器，默认使用全局实例
        """
        self.name = name
        self.version = version
        self.middleware = middleware or []
        self._tools: Dict[str, Callable] = {}
        self._prompts: Dict[str, Callable] = {}
        self._resources: Dict[str, Callable] = {}
        self._stats = stats or get_stats()
        self._protocol_handler = ProtocolHandler(
            tools=self._tools,
            prompts=self._prompts,
            resources=self._resources,
            middleware=self.middleware,
            stats=self._stats,
        )
        self._jsonrpc_handler = JSONRPCHandler(self._protocol_handler)

    def tool(self, name: Optional[str] = None, description: Optional[str] = None, input_schema: Optional[Dict] = None):
        """
        工具注册装饰器

        Args:
            name: 工具名称，默认使用函数名
            description: 工具描述
            input_schema: 输入参数模式

        Returns:
            装饰器函数

        Example:
            @server.tool(name="add", description="相加两个数字")
            async def add(a: int, b: int):
                return a + b
        """
        def decorator(func: Callable):
            tool_name = name or func.__name__
            func.__description__ = description
            func.__input_schema__ = input_schema or {}
            self._tools[tool_name] = func
            self._stats.register_tool(tool_name, description or "")
            return func
        return decorator

    def prompt(self, name: Optional[str] = None, description: Optional[str] = None, arguments: Optional[List[Dict]] = None):
        """
        提示词注册装饰器

        Args:
            name: 提示词名称，默认使用函数名
            description: 提示词描述
            arguments: 参数列表

        Returns:
            装饰器函数

        Example:
            @server.prompt(name="greeting", description="生成问候语")
            async def greeting(name: str):
                return [{"role": "user", "content": f"Hello, {name}!"}]
        """
        def decorator(func: Callable):
            prompt_name = name or func.__name__
            func.__description__ = description
            func.__arguments__ = arguments or []
            self._prompts[prompt_name] = func
            self._stats.register_prompt(prompt_name, description or "")
            return func
        return decorator

    def resource(self, uri: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, mime_type: Optional[str] = None):
        """
        资源注册装饰器

        Args:
            uri: 资源 URI，默认使用 "resource://{函数名}"
            name: 资源名称
            description: 资源描述
            mime_type: MIME 类型

        Returns:
            装饰器函数

        Example:
            @server.resource(uri="resource://config", description="服务器配置")
            async def config():
                return {"version": "1.0.0"}
        """
        def decorator(func: Callable):
            resource_uri = uri or f"resource://{func.__name__}"
            func.__name__ = name or func.__name__
            func.__description__ = description
            func.__mime_type__ = mime_type
            self._resources[resource_uri] = func
            self._stats.register_resource(resource_uri, description or "")
            return func
        return decorator

    def add_tool(self, name: str, func: Callable, description: Optional[str] = None, input_schema: Optional[Dict] = None):
        """
        手动添加工具

        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述
            input_schema: 输入参数模式
        """
        func.__description__ = description
        func.__input_schema__ = input_schema or {}
        self._tools[name] = func
        self._stats.register_tool(name, description or "")

    def add_prompt(self, name: str, func: Callable, description: Optional[str] = None, arguments: Optional[List[Dict]] = None):
        """
        手动添加提示词

        Args:
            name: 提示词名称
            func: 提示词函数
            description: 提示词描述
            arguments: 参数列表
        """
        func.__description__ = description
        func.__arguments__ = arguments or []
        self._prompts[name] = func
        self._stats.register_prompt(name, description or "")

    def add_resource(self, uri: str, func: Callable, name: Optional[str] = None, description: Optional[str] = None, mime_type: Optional[str] = None):
        """
        手动添加资源

        Args:
            uri: 资源 URI
            func: 资源函数
            name: 资源名称
            description: 资源描述
            mime_type: MIME 类型
        """
        func.__name__ = name or uri
        func.__description__ = description
        func.__mime_type__ = mime_type
        self._resources[uri] = func
        self._stats.register_resource(uri, description or "")

    def get_jsonrpc_handler(self):
        """
        获取 JSON-RPC 处理器

        Returns:
            JSONRPCHandler 实例
        """
        return self._jsonrpc_handler

    def get_protocol_handler(self):
        """
        获取协议处理器

        Returns:
            ProtocolHandler 实例
        """
        return self._protocol_handler
