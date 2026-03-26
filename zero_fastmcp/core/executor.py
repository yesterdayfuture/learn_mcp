"""
动态代码执行器
提供安全的 Python 代码编译和执行能力
支持通过字符串传输完整的异步函数定义并在远程执行
"""
import ast
import re
from typing import Any, Dict, Optional, Callable


class CodeExecutor:
    """
    代码执行器
    提供安全的 Python 代码编译和执行环境
    限制可使用的内置函数和模块
    """

    SAFE_BUILTINS = {
        "print": print,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "reversed": reversed,
        "any": any,
        "all": all,
        "isinstance": isinstance,
        "type": type,
        "getattr": getattr,
        "setattr": setattr,
        "hasattr": hasattr,
    }

    BLOCKED_MODULES = {
        "os", "sys", "subprocess", "socket", "urllib",
        "requests", "http", "ftplib", "telnetlib",
        "importlib", "pkgutil", "runpy",
        "ctypes", "cffi", "locale",
        "atexit", "gc", "sysconfig",
    }

    BLOCKED_NAMES = {"eval", "exec", "compile", "__import__", "open"}

    def __init__(self):
        """
        初始化代码执行器
        """
        self._compiled_functions: Dict[str, Callable] = {}

    def _validate_code(self, code: str) -> Optional[str]:
        """
        验证代码安全性

        Args:
            code: 待验证的代码字符串

        Returns:
            验证通过返回 None，失败返回错误信息
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"语法错误: {e}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in self.BLOCKED_MODULES:
                        return f"禁止导入模块: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in self.BLOCKED_MODULES:
                    return f"禁止导入模块: {node.module}"

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_NAMES:
                        return f"禁止调用函数: {node.func.id}"
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("__import__", "eval", "exec", "compile"):
                        return f"禁止调用方法: {node.func.attr}"

        return None

    def compile_function(self, code: str, func_name: Optional[str] = None) -> Optional[Callable]:
        """
        将代码字符串编译为独立的异步函数

        Args:
            code: 完整的异步函数定义，如:
                  "async def my_func(**kwargs): return kwargs['x'] + kwargs['y']"
            func_name: 可选的函数名，如果代码中包含函数定义则从代码中提取

        Returns:
            编译后的异步函数，失败返回 None
        """
        code = code.strip()

        if func_name is None:
            match = re.match(r"async\s+def\s+(\w+)", code)
            if match:
                func_name = match.group(1)
            else:
                return None

        error = self._validate_code(code)
        if error:
            return None

        safe_globals = {"__builtins__": self.SAFE_BUILTINS}

        try:
            exec(code, safe_globals, {})
            func = safe_globals.get(func_name)
            if func:
                self._compiled_functions[func_name] = func
            return func
        except Exception:
            return None

    def get_function(self, func_name: str) -> Optional[Callable]:
        """
        获取已编译的函数

        Args:
            func_name: 函数名称

        Returns:
            已编译的函数，未找到返回 None
        """
        return self._compiled_functions.get(func_name)


executor = CodeExecutor()
