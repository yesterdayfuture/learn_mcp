"""
服务端统计模块
追踪工具、提示词、资源的调用次数和调用历史
"""
import asyncio
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class CallRecord:
    """调用记录"""
    timestamp: float
    method: str
    name: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None


@dataclass
class ToolStats:
    """工具统计"""
    name: str
    description: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_call_time: Optional[float] = None
    history: List[CallRecord] = field(default_factory=list)


@dataclass
class PromptStats:
    """提示词统计"""
    name: str
    description: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_call_time: Optional[float] = None
    history: List[CallRecord] = field(default_factory=list)


@dataclass
class ResourceStats:
    """资源统计"""
    uri: str
    name: str
    read_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_read_time: Optional[float] = None
    history: List[CallRecord] = field(default_factory=list)


class ServerStats:
    """
    服务端统计管理器
    追踪所有工具、提示词、资源的调用情况
    """

    def __init__(self, max_history: int = 100):
        """
        初始化统计管理器

        Args:
            max_history: 每个项目保留的最大历史记录数
        """
        self.max_history = max_history
        self._tool_stats: Dict[str, ToolStats] = {}
        self._prompt_stats: Dict[str, PromptStats] = {}
        self._resource_stats: Dict[str, ResourceStats] = {}
        self._total_requests: int = 0
        self._start_time: float = time.time()
        self._lock = asyncio.Lock()

    def register_tool(self, name: str, description: str = ""):
        """
        注册工具到统计系统

        Args:
            name: 工具名称
            description: 工具描述
        """
        if name not in self._tool_stats:
            self._tool_stats[name] = ToolStats(name=name, description=description)

    def register_prompt(self, name: str, description: str = ""):
        """
        注册提示词到统计系统

        Args:
            name: 提示词名称
            description: 提示词描述
        """
        if name not in self._prompt_stats:
            self._prompt_stats[name] = PromptStats(name=name, description=description)

    def register_resource(self, uri: str, name: str = ""):
        """
        注册资源到统计系统

        Args:
            uri: 资源 URI
            name: 资源名称
        """
        if uri not in self._resource_stats:
            self._resource_stats[uri] = ResourceStats(uri=uri, name=name)

    def record_tool_call(self, name: str, arguments: Dict[str, Any], result: Any, success: bool, error: Optional[str] = None):
        """
        记录工具调用

        Args:
            name: 工具名称
            arguments: 调用参数
            result: 调用结果
            success: 是否成功
            error: 错误信息
        """
        if name in self._tool_stats:
            stats = self._tool_stats[name]
            stats.call_count += 1
            if success:
                stats.success_count += 1
            else:
                stats.error_count += 1
            stats.last_call_time = time.time()

            record = CallRecord(
                timestamp=time.time(),
                method="tool",
                name=name,
                arguments=arguments,
                result=str(result)[:200] if result else None,
                success=success,
                error=error
            )
            stats.history.append(record)
            if len(stats.history) > self.max_history:
                stats.history.pop(0)

    def record_prompt_call(self, name: str, arguments: Dict[str, Any], result: Any, success: bool, error: Optional[str] = None):
        """
        记录提示词调用

        Args:
            name: 提示词名称
            arguments: 调用参数
            result: 调用结果
            success: 是否成功
            error: 错误信息
        """
        if name in self._prompt_stats:
            stats = self._prompt_stats[name]
            stats.call_count += 1
            if success:
                stats.success_count += 1
            else:
                stats.error_count += 1
            stats.last_call_time = time.time()

            record = CallRecord(
                timestamp=time.time(),
                method="prompt",
                name=name,
                arguments=arguments,
                result=str(result)[:200] if result else None,
                success=success,
                error=error
            )
            stats.history.append(record)
            if len(stats.history) > self.max_history:
                stats.history.pop(0)

    def record_resource_read(self, uri: str, result: Any, success: bool, error: Optional[str] = None):
        """
        记录资源读取

        Args:
            uri: 资源 URI
            result: 读取结果
            success: 是否成功
            error: 错误信息
        """
        if uri in self._resource_stats:
            stats = self._resource_stats[uri]
            stats.read_count += 1
            if success:
                stats.success_count += 1
            else:
                stats.error_count += 1
            stats.last_read_time = time.time()

            record = CallRecord(
                timestamp=time.time(),
                method="resource",
                name=uri,
                arguments={},
                result=str(result)[:200] if result else None,
                success=success,
                error=error
            )
            stats.history.append(record)
            if len(stats.history) > self.max_history:
                stats.history.pop(0)

    async def get_summary(self) -> Dict[str, Any]:
        """
        获取统计摘要

        Returns:
            包含所有统计信息的字典
        """
        async with self._lock:
            uptime = time.time() - self._start_time

            tools = []
            for name, stats in self._tool_stats.items():
                tools.append({
                    "name": stats.name,
                    "description": stats.description,
                    "call_count": stats.call_count,
                    "success_count": stats.success_count,
                    "error_count": stats.error_count,
                    "last_call_time": stats.last_call_time,
                    "recent_history": [
                        {
                            "timestamp": r.timestamp,
                            "arguments": r.arguments,
                            "success": r.success,
                            "error": r.error
                        }
                        for r in stats.history[-5:]
                    ]
                })

            prompts = []
            for name, stats in self._prompt_stats.items():
                prompts.append({
                    "name": stats.name,
                    "description": stats.description,
                    "call_count": stats.call_count,
                    "success_count": stats.success_count,
                    "error_count": stats.error_count,
                    "last_call_time": stats.last_call_time,
                    "recent_history": [
                        {
                            "timestamp": r.timestamp,
                            "arguments": r.arguments,
                            "success": r.success,
                            "error": r.error
                        }
                        for r in stats.history[-5:]
                    ]
                })

            resources = []
            for uri, stats in self._resource_stats.items():
                resources.append({
                    "uri": stats.uri,
                    "name": stats.name,
                    "read_count": stats.read_count,
                    "success_count": stats.success_count,
                    "error_count": stats.error_count,
                    "last_read_time": stats.last_read_time,
                    "recent_history": [
                        {
                            "timestamp": r.timestamp,
                            "success": r.success,
                            "error": r.error
                        }
                        for r in stats.history[-5:]
                    ]
                })

            return {
                "uptime": uptime,
                "total_requests": self._total_requests,
                "tools": {
                    "count": len(tools),
                    "items": tools
                },
                "prompts": {
                    "count": len(prompts),
                    "items": prompts
                },
                "resources": {
                    "count": len(resources),
                    "items": resources
                }
            }


_global_stats = ServerStats()


def get_stats() -> ServerStats:
    """获取全局统计实例"""
    return _global_stats
