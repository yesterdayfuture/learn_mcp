"""
STDIO 模式演示服务端
通过标准输入输出进行 JSON-RPC 通信
适用于命令行工具、本地进程通信、stdin/stdout pipe

运行方式:
    python demo_stdio_server.py
或:
    cat requests.json | python demo_stdio_server.py
"""
import asyncio
import json
from zero_fastmcp import MCPServer
from zero_fastmcp.server.transports.stdio import run_stdio


server = MCPServer(
    name="demo-stdio-server",
    version="1.0.0",
)


@server.tool(name="add", description="相加两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def add(a: int, b: int):
    """加法工具"""
    return a + b


@server.tool(name="subtract", description="相减两个数字", input_schema={"a": {"type": "number"}, "b": {"type": "number"}})
async def subtract(a: int, b: int):
    """减法工具"""
    return a - b


@server.prompt(name="welcome", description="欢迎消息模板")
async def welcome_prompt(name: str):
    """欢迎提示词"""
    return [
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": f"欢迎 {name} 使用我们的服务！"},
    ]


@server.resource(uri="resource://config", name="config", description="配置文件", mime_type="application/json")
async def config_resource():
    """配置文件资源"""
    return {
        "app_name": "demo-stdio-server",
        "version": "1.0.0",
        "transport": "stdio"
    }


if __name__ == "__main__":
    print("Starting STDIO MCP Server...", file=__import__("sys").stderr)
    asyncio.run(run_stdio(server))
