# Zero FastMCP

基于 FastAPI 实现的轻量级 Model Context Protocol (MCP) Python 库。

## 功能特性

- **工具注册与调用** - 使用装饰器注册工具，支持远程调用
- **提示词注册与调用** - 动态管理和获取提示词
- **资源管理** - 注册和读取资源，支持 MIME 类型
- **多种传输协议** - HTTP、SSE（Server-Sent Events）、STDIO
- **中间件支持** - 认证、限流、日志、参数验证（洋葱模型）
- **洋葱模型中间件** - pre 阶段从外到内执行，post 阶段从内到外执行

## 安装

```bash
pip install fastapi uvicorn httpx pydantic sse-starlette
```

或从源码安装：

```bash
pip install -e .
```

## 快速开始

### HTTP 模式服务端

```python
from zero_fastmcp import MCPServer
from zero_fastmcp.server.transports.http import create_http_router
from fastapi import FastAPI
import uvicorn

server = MCPServer(name="my-server", version="1.0.0")

@server.tool(name="add", description="相加两个数字")
async def add(a: int, b: int):
    return a + b

@server.prompt(name="greeting", description="生成问候语")
async def greeting(name: str):
    return [{"role": "user", "content": f"你好，{name}！"}]

@server.resource(uri="resource://config", description="服务器配置")
async def config():
    return {"version": "1.0.0"}

app = FastAPI()
app.include_router(create_http_router(server))

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### HTTP 模式客户端

```python
import asyncio
from zero_fastmcp import MCPClient

async def main():
    async with MCPClient("http://localhost:8000") as client:
        tools = await client.list_tools()
        print(f"工具列表: {tools}")

        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(f"结果: {result}")

        prompts = await client.list_prompts()
        print(f"提示词列表: {prompts}")

        resources = await client.list_resources()
        print(f"资源列表: {resources}")

        contents = await client.read_resource("resource://config")
        print(f"配置: {contents}")

asyncio.run(main())
```

## 中间件（洋葱模型）

Zero FastMCP 采用洋葱模型执行中间件：

- **pre 阶段**：按顺序从第一个中间件执行到最后一个
- **执行实际函数**
- **post 阶段**：按逆序从最后一个中间件执行到第一个

```
middleware = [Logging, Auth, RateLimit]

执行顺序:
Logging.pre() → Auth.pre() → RateLimit.pre() → 函数执行 → RateLimit.post() → Auth.post() → Logging.post()
```

### 使用示例

```python
from zero_fastmcp.middleware import AuthMiddleware, RateLimitMiddleware, LoggingMiddleware

server = MCPServer(
    middleware=[
        LoggingMiddleware(),
        AuthMiddleware(api_key="secret-key"),
        RateLimitMiddleware(max_calls=100, window_seconds=60),
    ]
)
```

### 可用的中间件

| 中间件 | 描述 |
|--------|------|
| `AuthMiddleware` | API 密钥认证，验证 tool 和 prompt 调用 |
| `RateLimitMiddleware` | 请求限流，控制每个时间窗口内的调用次数 |
| `LoggingMiddleware` | 请求日志记录，记录入参和出参 |
| `ValidationMiddleware` | 参数验证，检查必填参数是否存在 |

### 自定义中间件

```python
from zero_fastmcp.middleware import Middleware

class CustomMiddleware(Middleware):
    async def pre(self, method: str, params: dict) -> bool:
        print(f"执行前: {method}")
        return True

    async def post(self, method: str, params: dict, result: any):
        print(f"执行后: {result}")
        return result
```

## 传输协议选项

### HTTP

适用于 Web 服务和 API 集成。

```python
from zero_fastmcp.server.transports.http import create_http_router
app.include_router(create_http_router(server))
```

### SSE (Server-Sent Events)

支持服务端主动向客户端推送事件。

```python
from zero_fastmcp.server.transports.sse import create_sse_router
app.include_router(create_sse_router(server))
```

### STDIO

通过标准输入输出进行通信，适用于命令行工具和本地进程通信。

```python
import asyncio
from zero_fastmcp.server.transports.stdio import run_stdio

asyncio.run(run_stdio(server))
```

## API 参考

### 服务端方法

| 方法 | 描述 |
|------|------|
| `@server.tool()` | 装饰器注册工具 |
| `@server.prompt()` | 装饰器注册提示词 |
| `@server.resource()` | 装饰器注册资源 |
| `server.add_tool()` | 编程方式添加工具 |
| `server.add_prompt()` | 编程方式添加提示词 |
| `server.add_resource()` | 编程方式添加资源 |

### 客户端方法

| 方法 | 描述 |
|------|------|
| `client.list_tools()` | 获取所有工具列表 |
| `client.call_tool()` | 调用指定工具 |
| `client.list_prompts()` | 获取所有提示词列表 |
| `client.get_prompt()` | 获取指定提示词 |
| `client.list_resources()` | 获取所有资源列表 |
| `client.read_resource()` | 读取指定资源 |
| `client.register_tool()` | 远程注册工具（支持自定义代码） |
| `client.register_prompt()` | 远程注册提示词（支持自定义代码） |
| `client.register_resource()` | 远程注册资源（支持自定义代码） |

## 远程注册与代码执行

支持通过客户端远程注册工具、提示词、资源，并可通过 Python 代码字符串在远程执行自定义逻辑。

### 注册带代码的工具

传递完整的异步函数定义：

```python
result = await client.register_tool(
    name="calculator",
    description="计算器",
    input_schema={"x": {"type": "number"}, "y": {"type": "number"}},
    code="""async def calculator(**kwargs):
    x = kwargs.get('x')
    y = kwargs.get('y')
    return x + y"""
)
await client.call_tool("calculator", {"x": 10, "y": 5})
```

### 注册带代码的提示词

```python
result = await client.register_prompt(
    name="greeting",
    description="问候提示词",
    arguments=[{"name": "name", "description": "姓名"}],
    code="""async def greeting(**kwargs):
    name = kwargs.get('name')
    return [{"role": "user", "content": f"你好，{name}！"}]"""
)
```

### 注册带代码的资源

```python
result = await client.register_resource(
    uri="resource://time",
    name="time",
    description="当前时间",
    code="""async def time():
    import datetime
    return {"now": datetime.datetime.now().isoformat()}"""
)
```

### 安全限制

代码执行器限制了以下危险操作：
- 禁止导入 `os`, `sys`, `subprocess`, `socket` 等系统模块
- 禁止使用 `eval`, `exec`, `compile`, `open` 等危险函数
- 支持超时和内存限制

## MCP 协议

实现遵循 [Model Context Protocol](https://modelcontextprotocol.io/) 规范：

- `tools/list` - 列出可用工具
- `tools/call` - 调用工具
- `prompts/list` - 列出可用提示词
- `prompts/get` - 获取提示词
- `resources/list` - 列出可用资源
- `resources/read` - 读取资源

所有通信使用 JSON-RPC 2.0 格式。

## 项目结构

```
zero_fastmcp/
├── zero_fastmcp/
│   ├── __init__.py            # 包入口
│   ├── core/                  # 核心协议实现
│   │   ├── __init__.py
│   │   ├── protocol.py        # JSON-RPC 协议处理（洋葱模型）
│   │   ├── transport.py       # 传输层基类
│   │   ├── executor.py        # 代码执行器（安全沙箱）
│   │   └── types.py           # 数据类型定义
│   ├── server/                # 服务端实现
│   │   ├── __init__.py
│   │   ├── server.py          # MCPServer 核心类
│   │   └── transports/        # 传输协议
│   │       ├── __init__.py
│   │       ├── http.py        # HTTP 传输
│   │       ├── sse.py         # SSE 传输
│   │       └── stdio.py       # STDIO 传输
│   ├── client/                # 客户端实现
│   │   ├── __init__.py
│   │   └── client.py          # MCPClient
│   ├── middleware/            # 中间件
│   │   ├── __init__.py
│   │   └── middleware.py      # 认证、限流、日志、验证
│   └── examples/              # 示例代码
│       ├── demo_server.py        # HTTP 服务端示例
│       ├── demo_client.py        # HTTP 客户端示例
│       ├── demo_sse_server.py    # SSE 服务端示例
│       ├── demo_sse_client.py    # SSE 客户端示例
│       ├── demo_stdio_server.py  # STDIO 服务端示例
│       ├── demo_stdio_client.py  # STDIO 客户端示例
│       ├── demo_register.py     # 远程注册示例
│       └── demo_dashboard.py    # 仪表盘示例
├── pyproject.toml
└── README.md
```

## 运行示例

```bash
# HTTP 模式
python -m zero_fastmcp.examples.demo_server   # 启动 HTTP 服务端
python -m zero_fastmcp.examples.demo_client    # 运行 HTTP 客户端

# SSE 模式
python -m zero_fastmcp.examples.demo_sse_server  # 启动 SSE 服务端
python -m zero_fastmcp.examples.demo_sse_client   # 运行 SSE 客户端

# STDIO 模式
python -m zero_fastmcp.examples.demo_stdio_server  # 启动 STDIO 服务端
python -m zero_fastmcp.examples.demo_stdio_client  # 运行 STDIO 客户端

# 远程注册与代码执行（需要先启动 HTTP 服务端）
python -m zero_fastmcp.examples.demo_register  # 运行远程注册演示

# 仪表盘（需要先启动 HTTP 或 SSE 服务端）
python -m zero_fastmcp.examples.demo_dashboard  # 启动仪表盘服务端
# 访问 http://localhost:8000/dashboard 查看界面
```

## 仪表盘

HTTP 和 SSE 服务端内置了仪表盘功能，可通过浏览器访问：

- **HTTP 模式**: http://localhost:8000/dashboard
- **SSE 模式**: http://localhost:8000/dashboard

仪表盘功能：
- 查看所有工具、提示词、资源的数量和详情
- 查看每个项目的调用次数和成功率
- 查看最近的调用历史记录
- 自动刷新（每10秒）

## License

MIT
