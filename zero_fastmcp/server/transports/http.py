"""
HTTP 传输适配器
通过 HTTP POST 请求接收 JSON-RPC 消息
适用于 Web 服务和 API 集成
"""
import os
from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from typing import Optional
from ..server import MCPServer
from ..stats import get_stats


def create_http_router(server: MCPServer):
    """
    创建 HTTP 传输路由

    Args:
        server: MCP 服务端实例

    Returns:
        FastAPI 路由

    路由说明:
        POST /mcp - 接收 JSON-RPC 消息并返回响应
        GET / - 获取服务端信息或重定向到仪表盘
        GET /dashboard - 仪表盘页面
        GET /stats - 统计数据接口
    """
    router = APIRouter()

    @router.post("/mcp")
    async def mcp_endpoint(request: Request):
        """
        MCP 端点，接收 JSON-RPC 请求并返回响应

        请求体应为 JSON-RPC 2.0 格式的请求
        """
        body = await request.body()
        message = body.decode("utf-8")
        handler = server.get_jsonrpc_handler()
        response = await handler.handle_message(message)
        return Response(content=response, media_type="application/json")

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
