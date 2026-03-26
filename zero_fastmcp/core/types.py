"""
MCP (Model Context Protocol) 核心数据类型定义
提供工具、提示词、资源等数据结构
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict, Union, Callable
from enum import Enum


class JSONRPCVersion(str, Enum):
    """JSON-RPC 协议版本"""
    V2_0 = "2.0"


class Tool(BaseModel):
    """工具定义"""
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    callback: Optional[Callable] = None


class Prompt(BaseModel):
    """提示词定义"""
    name: str
    description: Optional[str] = None
    arguments: List[Dict[str, Any]] = Field(default_factory=list)
    callback: Optional[Callable] = None


class Resource(BaseModel):
    """资源定义"""
    uri: str
    name: Optional[str] = None
    description: Optional[str] = None
    mime_type: Optional[str] = None
    callback: Optional[Callable] = None


class MCPRequest(BaseModel):
    """JSON-RPC 请求格式"""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    id: Union[str, int, None] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """JSON-RPC 响应格式"""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    id: Union[str, int, None] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPMessage(BaseModel):
    """MCP 消息格式（统一请求和响应）"""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    id: Union[str, int, None] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class CallToolRequest(BaseModel):
    """调用工具请求"""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class CallToolResponse(BaseModel):
    """调用工具响应"""
    content: List[Dict[str, Any]]
    is_error: Optional[bool] = None


class GetPromptRequest(BaseModel):
    """获取提示词请求"""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class GetPromptResponse(BaseModel):
    """获取提示词响应"""
    messages: List[Dict[str, Any]]


class ReadResourceRequest(BaseModel):
    """读取资源请求"""
    uri: str


class ReadResourceResponse(BaseModel):
    """读取资源响应"""
    contents: List[Dict[str, Any]]


class ListToolsRequest(BaseModel):
    """列出工具请求"""
    pass


class ListToolsResponse(BaseModel):
    """列出工具响应"""
    tools: List[Dict[str, Any]]


class ListPromptsRequest(BaseModel):
    """列出提示词请求"""
    pass


class ListPromptsResponse(BaseModel):
    """列出提示词响应"""
    prompts: List[Dict[str, Any]]


class ListResourcesRequest(BaseModel):
    """列出资源请求"""
    pass


class ListResourcesResponse(BaseModel):
    """列出资源响应"""
    resources: List[Dict[str, Any]]
