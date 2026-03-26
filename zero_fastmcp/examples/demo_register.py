"""
远程注册演示
展示如何通过客户端远程注册工具、提示词、资源
支持通过传递完整的异步函数定义在远程执行

运行方式:
    1. 先启动服务端: python -m zero_fastmcp.examples.demo_server
    2. 再运行客户端: python -m zero_fastmcp.examples.demo_register
"""
import asyncio
from zero_fastmcp import MCPClient


async def main():
    """
    主函数：演示远程注册功能（支持自定义代码执行）
    """
    async with MCPClient("http://localhost:8000") as client:
        print("=== 远程注册工具（带自定义代码） ===")

        result = await client.register_tool(
            name="python_calc",
            description="Python 计算器",
            input_schema={"x": {"type": "number"}, "y": {"type": "number"}, "operation": {"type": "string"}},
            code="""async def python_calc(**kwargs):
    x = kwargs.get('x')
    y = kwargs.get('y')
    operation = kwargs.get('operation')

    if operation == 'add':
        return x + y
    elif operation == 'subtract':
        return x - y
    elif operation == 'multiply':
        return x * y
    elif operation == 'divide':
        if y == 0:
            raise ValueError("除数不能为0")
        return x / y
    else:
        raise ValueError(f"未知操作: {operation}")"""
        )
        print(f"注册工具结果: {result}")

        print("\n--- 调用远程工具: 10 + 5 ---")
        result = await client.call_tool("python_calc", {"x": 10, "y": 5, "operation": "add"})
        print(f"结果: {result}")

        print("\n--- 调用远程工具: 10 * 3 ---")
        result = await client.call_tool("python_calc", {"x": 10, "y": 3, "operation": "multiply"})
        print(f"结果: {result}")
        print()

        print("=== 远程注册提示词（带自定义代码） ===")

        result = await client.register_prompt(
            name="code_review",
            description="代码审查提示词",
            arguments=[
                {"name": "language", "description": "编程语言", "required": True},
                {"name": "code", "description": "代码内容", "required": True}
            ],
            code="""async def code_review(**kwargs):
    language = kwargs.get('language')
    code = kwargs.get('code')
    return [
        {"role": "system", "content": f"你是一个专业的 {language} 开发者，负责审查代码。"},
        {"role": "user", "content": f"请审查以下 {language} 代码并提供改进建议:\\n\\n{code}"}
    ]"""
        )
        print(f"注册提示词结果: {result}")

        result = await client.get_prompt("code_review", {"language": "Python", "code": "def foo(): pass"})
        print(f"获取提示词内容: {result}")
        print()

        print("=== 远程注册资源（带自定义代码） ===")

        result = await client.register_resource(
            uri="resource://server_time",
            name="server_time",
            description="服务器当前时间",
            mime_type="application/json",
            code="""async def server_time():
    import datetime
    return {"timestamp": datetime.datetime.now().isoformat()}"""
        )
        print(f"注册资源结果: {result}")

        contents = await client.read_resource("resource://server_time")
        print(f"读取远程资源: {contents}")
        print()

        print("=== 查看所有工具 ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', '无描述')}")

        print("\n=== 查看所有提示词 ===")
        prompts = await client.list_prompts()
        for prompt in prompts:
            print(f"  - {prompt['name']}: {prompt.get('description', '无描述')}")

        print("\n=== 查看所有资源 ===")
        resources = await client.list_resources()
        for resource in resources:
            print(f"  - {resource['uri']}: {resource.get('description', '无描述')}")


if __name__ == "__main__":
    asyncio.run(main())
