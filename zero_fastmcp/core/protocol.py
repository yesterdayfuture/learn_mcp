"""
MCP 协议处理器
实现 JSON-RPC 2.0 协议，处理工具、提示词、资源的调用
采用洋葱模型执行中间件
支持远程代码执行
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from .types import (
    MCPRequest,
    MCPResponse,
)
from .executor import CodeExecutor


class ProtocolHandler:
    """
    MCP 协议处理器
    负责处理所有 MCP 方法的请求和响应
    """

    def __init__(
        self,
        tools: Dict[str, Callable],
        prompts: Dict[str, Callable],
        resources: Dict[str, Callable],
        middleware: Optional[List] = None,
        stats: Optional[Any] = None,
    ):
        """
        初始化协议处理器

        Args:
            tools: 工具字典，键为工具名，值为可调用函数
            prompts: 提示词字典，键为提示词名，值为可调用函数
            resources: 资源字典，键为资源 URI，值为可调用函数
            middleware: 中间件列表，用于请求/响应处理
            stats: 统计管理器
        """
        self.tools = tools
        self.prompts = prompts
        self.resources = resources
        self.middleware = middleware or []
        self._executor = CodeExecutor()
        self._stats = stats

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        处理 MCP 请求

        Args:
            request: MCP 请求对象

        Returns:
            MCP 响应对象
        """
        method = request.method

        if method == "tools/list":
            return await self._list_tools(request)
        elif method == "tools/call":
            return await self._call_tool(request)
        elif method == "tools/register":
            return await self._register_tool(request)
        elif method == "prompts/list":
            return await self._list_prompts(request)
        elif method == "prompts/get":
            return await self._get_prompt(request)
        elif method == "prompts/register":
            return await self._register_prompt(request)
        elif method == "resources/list":
            return await self._list_resources(request)
        elif method == "resources/read":
            return await self._read_resource(request)
        elif method == "resources/register":
            return await self._register_resource(request)
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method not found: {method}"},
            )

    async def _run_pre_middleware(self, method: str, params: Dict[str, Any]) -> bool:
        """
        执行所有中间件的 pre 阶段（洋葱模型外层到内层）

        Args:
            method: 方法名（如 "tool", "prompt", "resource"）
            params: 方法参数

        Returns:
            所有中间件都返回 True 时为 True，否则为 False
        """
        for mw in self.middleware:
            result = await mw.pre(method, params)
            if not result:
                return False
        return True

    async def _run_post_middleware(self, method: str, params: Dict[str, Any], result: Any) -> Any:
        """
        执行所有中间件的 post 阶段（洋葱模型内层到外层）

        Args:
            method: 方法名
            params: 方法参数
            result: 原始结果

        Returns:
            经过所有中间件处理后的结果
        """
        for mw in reversed(self.middleware):
            result = await mw.post(method, params, result)
        return result

    async def _list_tools(self, request: MCPRequest) -> MCPResponse:
        """
        处理 tools/list 请求，列出所有可用工具

        Args:
            request: MCP 请求对象

        Returns:
            包含工具列表的 MCP 响应
        """
        params = {}

        if not await self._run_pre_middleware("tools/list", params):
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Middleware rejected tools/list"},
            )

        tools_list = []
        for name, tool in self.tools.items():
            tools_list.append({
                "name": name,
                "description": getattr(tool, "__description__", None),
                "input_schema": getattr(tool, "__input_schema__", {}),
            })

        result = {"tools": tools_list}
        result = await self._run_post_middleware("tools/list", params, result)
        return MCPResponse(id=request.id, result=result)

    async def _call_tool(self, request: MCPRequest) -> MCPResponse:
        """
        处理 tools/call 请求，调用指定工具

        Args:
            request: MCP 请求对象

        Returns:
            包含工具执行结果的 MCP 响应
        """
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not await self._run_pre_middleware("tool", {"name": name, "arguments": arguments}):
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Middleware rejected tool call"},
            )

        if name not in self.tools:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Tool not found: {name}"},
            )

        try:
            tool_result = await self.tools[name](**arguments)
            result = {"content": [{"type": "text", "text": str(tool_result)}]}
            result = await self._run_post_middleware("tool", {"name": name, "arguments": arguments}, result)

            if self._stats:
                self._stats.record_tool_call(name, arguments, tool_result, True)

            return MCPResponse(id=request.id, result=result)
        except Exception as e:
            if self._stats:
                self._stats.record_tool_call(name, arguments, str(e), False, str(e))
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": str(e)},
            )

    async def _register_tool(self, request: MCPRequest) -> MCPResponse:
        """
        处理 tools/register 请求，远程注册工具（支持自定义代码）

        Args:
            request: MCP 请求对象

        Returns:
            注册结果
        """
        params = request.params or {}
        name = params.get("name")
        description = params.get("description", "")
        input_schema = params.get("input_schema", {})
        code = params.get("code", "")

        if not name:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Tool name is required"},
            )

        if code:
            func = self._executor.compile_function(code)
            if func is None:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32602, "message": "Invalid code: code validation failed"},
                )

            func.__description__ = description
            func.__input_schema__ = input_schema
            func.__code__ = code
            self.tools[name] = func
        else:
            async def dynamic_tool(**kwargs):
                return kwargs.get("_result", None)

            dynamic_tool.__description__ = description
            dynamic_tool.__input_schema__ = input_schema
            self.tools[name] = dynamic_tool

        if self._stats:
            self._stats.register_tool(name, description)

        return MCPResponse(id=request.id, result={"registered": True, "name": name})

    async def _register_prompt(self, request: MCPRequest) -> MCPResponse:
        """
        处理 prompts/register 请求，远程注册提示词（支持自定义代码）

        Args:
            request: MCP 请求对象

        Returns:
            注册结果
        """
        params = request.params or {}
        name = params.get("name")
        description = params.get("description", "")
        arguments = params.get("arguments", [])
        code = params.get("code", "")

        if not name:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Prompt name is required"},
            )

        if code:
            func = self._executor.compile_function(code)
            if func is None:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32602, "message": "Invalid code: code validation failed"},
                )

            func.__description__ = description
            func.__arguments__ = arguments
            func.__code__ = code
            self.prompts[name] = func
        else:
            async def dynamic_prompt(**kwargs):
                return [{"role": "user", "content": kwargs.get("_content", "")}]

            dynamic_prompt.__description__ = description
            dynamic_prompt.__arguments__ = arguments
            self.prompts[name] = dynamic_prompt

        if self._stats:
            self._stats.register_prompt(name, description)

        return MCPResponse(id=request.id, result={"registered": True, "name": name})

    async def _register_resource(self, request: MCPRequest) -> MCPResponse:
        """
        处理 resources/register 请求，远程注册资源（支持自定义代码）

        Args:
            request: MCP 请求对象

        Returns:
            注册结果
        """
        params = request.params or {}
        uri = params.get("uri")
        name = params.get("name", "")
        description = params.get("description", "")
        mime_type = params.get("mime_type")
        code = params.get("code", "")

        if not uri:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Resource URI is required"},
            )

        if code:
            func = self._executor.compile_function(code)
            if func is None:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32602, "message": "Invalid code: code validation failed"},
                )

            func.__name__ = name
            func.__description__ = description
            func.__mime_type__ = mime_type
            func.__code__ = code
            self.resources[uri] = func
        else:
            async def dynamic_resource():
                return params.get("_content", {})

            dynamic_resource.__name__ = name
            dynamic_resource.__description__ = description
            dynamic_resource.__mime_type__ = mime_type
            self.resources[uri] = dynamic_resource

        if self._stats:
            self._stats.register_resource(uri, name or description)

        return MCPResponse(id=request.id, result={"registered": True, "uri": uri})

    async def _list_prompts(self, request: MCPRequest) -> MCPResponse:
        """
        处理 prompts/list 请求，列出所有可用提示词

        Args:
            request: MCP 请求对象

        Returns:
            包含提示词列表的 MCP 响应
        """
        params = {}

        if not await self._run_pre_middleware("prompts/list", params):
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Middleware rejected prompts/list"},
            )

        prompts_list = []
        for name, prompt in self.prompts.items():
            prompts_list.append({
                "name": name,
                "description": getattr(prompt, "__description__", None),
                "arguments": getattr(prompt, "__arguments__", []),
            })

        result = {"prompts": prompts_list}
        result = await self._run_post_middleware("prompts/list", params, result)
        return MCPResponse(id=request.id, result=result)

    async def _get_prompt(self, request: MCPRequest) -> MCPResponse:
        """
        处理 prompts/get 请求，获取指定提示词

        Args:
            request: MCP 请求对象

        Returns:
            包含提示词内容的 MCP 响应
        """
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not await self._run_pre_middleware("prompt", {"name": name, "arguments": arguments}):
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Middleware rejected prompt call"},
            )

        if name not in self.prompts:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Prompt not found: {name}"},
            )

        try:
            prompt_result = await self.prompts[name](**arguments)
            result = {"messages": prompt_result}
            result = await self._run_post_middleware("prompt", {"name": name, "arguments": arguments}, result)

            if self._stats:
                self._stats.record_prompt_call(name, arguments, prompt_result, True)

            return MCPResponse(id=request.id, result=result)
        except Exception as e:
            if self._stats:
                self._stats.record_prompt_call(name, arguments, str(e), False, str(e))
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": str(e)},
            )

    async def _list_resources(self, request: MCPRequest) -> MCPResponse:
        """
        处理 resources/list 请求，列出所有可用资源

        Args:
            request: MCP 请求对象

        Returns:
            包含资源列表的 MCP 响应
        """
        params = {}

        if not await self._run_pre_middleware("resources/list", params):
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Middleware rejected resources/list"},
            )

        resources_list = []
        for uri, resource in self.resources.items():
            resources_list.append({
                "uri": uri,
                "name": getattr(resource, "__name__", uri),
                "description": getattr(resource, "__description__", None),
                "mime_type": getattr(resource, "__mime_type__", None),
            })

        result = {"resources": resources_list}
        result = await self._run_post_middleware("resources/list", params, result)
        return MCPResponse(id=request.id, result=result)

    async def _read_resource(self, request: MCPRequest) -> MCPResponse:
        """
        处理 resources/read 请求，读取指定资源

        Args:
            request: MCP 请求对象

        Returns:
            包含资源内容的 MCP 响应
        """
        params = request.params or {}
        uri = params.get("uri")

        if not await self._run_pre_middleware("resource", {"uri": uri}):
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Middleware rejected resource read"},
            )

        if uri not in self.resources:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Resource not found: {uri}"},
            )

        try:
            resource_result = await self.resources[uri]()
            result = {"contents": [{"uri": uri, "content": resource_result}]}
            result = await self._run_post_middleware("resource", {"uri": uri}, result)

            if self._stats:
                self._stats.record_resource_read(uri, resource_result, True)

            return MCPResponse(id=request.id, result=result)
        except Exception as e:
            if self._stats:
                self._stats.record_resource_read(uri, str(e), False, str(e))
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": str(e)},
            )
