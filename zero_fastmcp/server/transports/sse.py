"""
SSE (Server-Sent Events) 传输适配器
支持服务端推送事件到客户端
客户端先建立 SSE 连接，再通过 HTTP POST 发送请求，结果通过 SSE 推送
"""
import os
import asyncio
import json
from typing import Optional, Callable, Set, Dict
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse
from ..server import MCPServer
from ..stats import get_stats


def create_sse_router(server: MCPServer):
    """
    创建 SSE 传输路由

    Args:
        server: MCP 服务端实例

    Returns:
        FastAPI 路由

    路由说明:
        GET /sse - 建立 SSE 连接，接收服务端推送的事件
        POST /message - 接收客户端消息，响应通过 SSE 推送
        GET / - 获取服务端信息或重定向到仪表盘
        GET /dashboard - 仪表盘页面
        GET /stats - 统计数据接口
    """
    router = APIRouter()
    clients: Set[asyncio.Queue] = set()
    pending_responses: Dict[str, asyncio.Queue] = {}

    @router.get("/sse")
    async def sse_endpoint(request: Request):
        """
        SSE 端点，建立持久连接接收服务端事件
        客户端通过此连接接收工具调用结果等事件
        """
        client_queue = asyncio.Queue()
        client_id = id(client_queue)
        clients.add(client_queue)
        pending_responses[str(client_id)] = client_queue

        async def event_generator():
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(client_queue.get(), timeout=30)
                        yield message
                    except asyncio.TimeoutError:
                        yield {"event": "ping", "data": "{}"}
            except asyncio.CancelledError:
                pass
            finally:
                clients.discard(client_queue)
                pending_responses.pop(str(client_id), None)

        return EventSourceResponse(event_generator())

    @router.post("/message")
    async def message_endpoint(request: Request):
        """
        消息端点，接收 JSON-RPC 消息
        响应通过 SSE 通道推送给客户端
        """
        body = await request.body()
        message = body.decode("utf-8")
        handler = server.get_jsonrpc_handler()
        response = await handler.handle_message(message)

        response_event = {"event": "message", "data": response}

        if clients:
            for client in list(clients):
                await client.put(response_event)

        return JSONResponse(content=json.loads(response))

    @router.get("/")
    async def root():
        """
        根端点，重定向到仪表盘
        """
        return HTMLResponse(content='<html><head><meta charset="utf-8"><script>window.location.href="/dashboard";</script></head><body>正在跳转到仪表盘...</body></html>')

    @router.get("/dashboard")
    async def dashboard():
        """
        仪表盘页面
        """
        dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard.html")
        return FileResponse(dashboard_path)

    @router.get("/stats")
    async def stats():
        """
        统计接口
        """
        stats_manager = get_stats()
        summary = await stats_manager.get_summary()
        return summary

    return router
