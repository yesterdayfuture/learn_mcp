"""
仪表盘演示
展示 MCP 服务端管理界面
可查看所有工具、提示词、资源的数量、详情、调用次数和调用历史

运行方式:
    1. 启动 HTTP 服务端: python -m zero_fastmcp.examples.demo_dashboard
    2. 访问仪表盘: http://localhost:8000/dashboard
"""
import asyncio
import uvicorn
from fastapi import FastAPI
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
    """相加工具"""
    return a + b


@server.tool(name="subtract", description="相减两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def subtract(a: int, b: int):
    """相减工具"""
    return a - b


@server.tool(name="multiply", description="相乘两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def multiply(a: int, b: int):
    """相乘工具"""
    return a * b


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
    app = FastAPI()
    app.include_router(create_http_router(server))

    print("Starting MCP Server with Dashboard on http://localhost:8000")
    print("Access Dashboard: http://localhost:8000/dashboard")
    uvicorn.run(app, host="0.0.0.0", port=8000)
