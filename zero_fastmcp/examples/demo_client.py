"""
演示客户端
展示如何使用 MCP 客户端调用工具、提示词和资源
"""
import asyncio
from zero_fastmcp.client.client import MCPClient


async def main():
    """主函数：演示 MCP 客户端的各种功能"""
    async with MCPClient("http://localhost:8000") as client:
        api_key = "secret-key"

        print("=== 列出所有工具 ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"工具名: {tool['name']} - 描述: {tool.get('description', '无')}")
            print(f"  输入模式: {tool.get('input_schema', {})}")
            print()

        print("=== 调用工具 (add) ===")
        result = await client.call_tool("add", {"a": 5, "b": 3, "api_key": api_key})
        print(f"结果: {result}")
        print()

        print("=== 调用工具 (greet) ===")
        result = await client.call_tool("greet", {"name": "Alice", "api_key": api_key})
        print(f"结果: {result}")
        print()

        print("=== 列出所有提示词 ===")
        prompts = await client.list_prompts()
        for prompt in prompts:
            print(f"提示词名: {prompt['name']} - 描述: {prompt.get('description', '无')}")
            print()

        print("=== 获取提示词 ===")
        messages = await client.get_prompt("welcome", {"name": "Bob", "api_key": api_key})
        print(f"消息: {messages}")
        print()

        print("=== 列出所有资源 ===")
        resources = await client.list_resources()
        for resource in resources:
            print(f"资源 URI: {resource['uri']} - 描述: {resource.get('description', '无')}")
            print()

        print("=== 读取资源 ===")
        contents = await client.read_resource("resource://greeting")
        print(f"内容: {contents}")


if __name__ == "__main__":
    asyncio.run(main())
