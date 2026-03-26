"""
演示服务端
展示如何使用 MCP 服务端注册工具、提示词和资源
以及如何配置中间件
"""
import asyncio
from zero_fastmcp import MCPServer
from zero_fastmcp.server.transports.http import create_http_router
from zero_fastmcp.middleware.middleware import AuthMiddleware, LoggingMiddleware, RateLimitMiddleware


server = MCPServer(
    name="demo-server",
    version="1.0.0",
    middleware=[
        LoggingMiddleware(),
        AuthMiddleware(api_key="secret-key"),
        RateLimitMiddleware(max_calls=10, window_seconds=60),
    ]
)


@server.tool(name="add", description="相加两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def add(a: int, b: int):
    """加法工具"""
    return a + b


@server.tool(name="greet", description="生成问候语", input_schema={"name": {"type": "string"}})
async def greet(name: str):
    """问候工具"""
    return f"Hello, {name}!"


@server.prompt(name="welcome", description="欢迎消息模板")
async def welcome_prompt(name: str):
    """欢迎提示词"""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Welcome {name} to our service!"},
    ]


@server.resource(uri="resource://greeting", name="greeting", description="问候资源", mime_type="text/plain")
async def greeting_resource():
    """问候资源"""
    return "Hello, World!"


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(create_http_router(server))

    print("Starting MCP Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
