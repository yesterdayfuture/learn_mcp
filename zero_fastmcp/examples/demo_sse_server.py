"""
SSE 模式演示服务端
通过 Server-Sent Events 传输协议提供服务
支持服务端主动向客户端推送事件
"""
from zero_fastmcp import MCPServer
from zero_fastmcp.server.transports.sse import create_sse_router
from fastapi import FastAPI
import uvicorn


server = MCPServer(
    name="demo-sse-server",
    version="1.0.0",
)


@server.tool(name="add", description="相加两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def add(a: int, b: int):
    """加法工具"""
    return a + b


@server.tool(name="multiply", description="相乘两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def multiply(a: int, b: int):
    """乘法工具"""
    return a * b


@server.prompt(name="greeting", description="生成问候语")
async def greeting_prompt(name: str):
    """问候提示词"""
    return [
        {"role": "user", "content": f"你好，{name}！有什么我可以帮助你的吗？"}
    ]


@server.resource(uri="resource://info", name="info", description="服务器信息", mime_type="application/json")
async def info_resource():
    """服务器信息资源"""
    return {"name": "demo-sse-server", "version": "1.0.0", "transport": "sse"}


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(create_sse_router(server))

    print("Starting SSE MCP Server on http://localhost:8000")
    print("SSE endpoint: http://localhost:8000/sse")
    print("Message endpoint: http://localhost:8000/message")
    uvicorn.run(app, host="0.0.0.0", port=8000)
