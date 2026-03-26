"""
中间件模块
提供请求/响应拦截处理功能
采用洋葱模型：pre 阶段从外到内执行，post 阶段从内到外执行
"""
from typing import Callable, Awaitable, Dict, Any, List, Optional


class Middleware:
    """
    中间件基类
    子类需实现 pre 和 post 方法
    """

    async def pre(self, method: str, params: Dict[str, Any]) -> Any:
        """
        前置处理阶段（在目标函数执行之前）

        Args:
            method: 方法类型（如 "tool", "prompt", "resource"）
            params: 方法参数

        Returns:
            返回 True 继续执行，返回 False 拒绝请求
        """
        return True

    async def post(self, method: str, params: Dict[str, Any], result: Any) -> Any:
        """
        后置处理阶段（在目标函数执行之后）

        Args:
            method: 方法类型
            params: 方法参数
            result: 原始结果

        Returns:
            处理后的结果
        """
        return result


class AuthMiddleware(Middleware):
    """
    认证中间件
    验证 API 密钥是否正确
    """

    def __init__(self, api_key: str):
        """
        初始化认证中间件

        Args:
            api_key: 预期的 API 密钥
        """
        self.api_key = api_key

    async def pre(self, method: str, params: Dict[str, Any]) -> bool:
        """
        验证 API 密钥

        Args:
            method: 方法类型
            params: 参数字典，需包含 arguments.api_key

        Returns:
            密钥匹配返回 True，否则返回 False
        """
        if method in ["tool", "prompt"]:
            arguments = params.get("arguments", {})
            provided_key = arguments.get("api_key")
            if provided_key != self.api_key:
                return False
            arguments.pop("api_key", None)
        return True

    async def post(self, method: str, params: Dict[str, Any], result: Any) -> Any:
        """
        后置处理（不做任何修改）
        """
        return result


class RateLimitMiddleware(Middleware):
    """
    限流中间件
    限制每个时间窗口内的请求次数
    """

    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        """
        初始化限流中间件

        Args:
            max_calls: 时间窗口内允许的最大调用次数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: Dict[str, List[float]] = {}

    async def pre(self, method: str, params: Dict[str, Any]) -> bool:
        """
        检查是否超过限流阈值

        Args:
            method: 方法类型
            params: 参数字典

        Returns:
            未超过限流返回 True，否则返回 False
        """
        key = params.get("name") or params.get("uri") or "default"
        now = __import__("time").time()

        if key not in self._calls:
            self._calls[key] = []

        self._calls[key] = [t for t in self._calls[key] if now - t < self.window_seconds]

        if len(self._calls[key]) >= self.max_calls:
            return False

        self._calls[key].append(now)
        return True

    async def post(self, method: str, params: Dict[str, Any], result: Any) -> Any:
        """
        后置处理（不做任何修改）
        """
        return result


class LoggingMiddleware(Middleware):
    """
    日志中间件
    记录请求和响应的日志
    """

    def __init__(self, logger_name: str = "mcp"):
        """
        初始化日志中间件

        Args:
            logger_name: 日志记录器名称
        """
        self.logger_name = logger_name
        self.logger = __import__("logging").getLogger(logger_name)

    async def pre(self, method: str, params: Dict[str, Any]) -> bool:
        """
        记录请求日志
        """
        self.logger.info(f"→ MCP {method} called with params: {params}")
        return True

    async def post(self, method: str, params: Dict[str, Any], result: Any) -> Any:
        """
        记录响应日志
        """
        self.logger.info(f"← MCP {method} returned: {result}")
        return result


class ValidationMiddleware(Middleware):
    """
    验证中间件
    检查必填参数是否存在
    """

    def __init__(self, required_fields: Dict[str, List[str]]):
        """
        初始化验证中间件

        Args:
            required_fields: 必填字段配置，键为方法类型，值为必填字段列表
                           例如: {"tool": ["name"], "prompt": ["name"]}
        """
        self.required_fields = required_fields

    async def pre(self, method: str, params: Dict[str, Any]) -> bool:
        """
        验证必填参数

        Args:
            method: 方法类型
            params: 参数字典

        Returns:
            所有必填参数都存在返回 True，否则返回 False
        """
        if method in self.required_fields:
            required = self.required_fields[method]
            arguments = params.get("arguments", {})
            for field in required:
                if field not in arguments:
                    return False
        return True

    async def post(self, method: str, params: Dict[str, Any], result: Any) -> Any:
        """
        后置处理（不做任何修改）
        """
        return result


def create_middleware(middleware_class: type, **kwargs) -> Middleware:
    """
    中间件工厂函数

    Args:
        middleware_class: 中间件类
        **kwargs: 传递给中间件构造函数的参数

    Returns:
        中间件实例

    Example:
        auth = create_middleware(AuthMiddleware, api_key="secret")
    """
    return middleware_class(**kwargs)
