import json
import os
from pathlib import Path
from typing import Any
import asyncio

class FilesystemMCPServer:
    """文件系统MCP服务器"""
    
    def __init__(self, allowed_directories: list[str]):
        """初始化服务器
        
        Args:
            allowed_directories: 允许访问的目录列表(白名单)
        """
        self.allowed_dirs = [Path(d).resolve() for d in allowed_directories]
        self.tools = self._register_tools()
    
    def _register_tools(self) -> dict:
        """注册可用工具"""
        return {
            "read_file": {
                "description": "读取指定文件的内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["path"]
                }
            },
            "search_files": {
                "description": "在目录中搜索包含关键词的文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "搜索目录"},
                        "keyword": {"type": "string", "description": "搜索关键词"}
                    },
                    "required": ["directory", "keyword"]
                }
            },
            "list_directory": {
                "description": "列出目录中的所有文件和子目录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "目录路径"}
                    },
                    "required": ["path"]
                }
            }
        }
    
    def _is_path_allowed(self, path: str) -> bool:
        """检查路径是否在允许的目录中"""
        target_path = Path(path).resolve()
        return any(
            target_path == allowed_dir or 
            allowed_dir in target_path.parents
            for allowed_dir in self.allowed_dirs
        )

    async def read_file(self, path: str) -> dict:
        """读取文件内容"""
        if not self._is_path_allowed(path):
            return {"error": f"访问被拒绝:{path}不在允许的目录中"}
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                return {"error": f"文件不存在:{path}"}
            
            # 限制文件大小(最大1MB)
            if file_path.stat().st_size > 1024 * 1024:
                return {"error": "文件过大(>1MB)"}
            
            content = file_path.read_text(encoding='utf-8')
            return {
                "path": str(file_path),
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {"error": f"读取失败:{str(e)}"}
    
    async def search_files(self, directory: str, keyword: str) -> dict:
        """搜索包含关键词的文件"""
        if not self._is_path_allowed(directory):
            return {"error": f"访问被拒绝:{directory}不在允许的目录中"}
        
        try:
            dir_path = Path(directory)
            if not dir_path.is_dir():
                return {"error": f"不是有效目录:{directory}"}
            
            results = []
            # 递归搜索(限制深度为3层)
            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and len(file_path.parts) - len(dir_path.parts) <= 3:
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        if keyword.lower() in content.lower():
                            results.append({
                                "path": str(file_path),
                                "matches": content.lower().count(keyword.lower())
                            })
                    except:
                        continue  # 跳过无法读取的文件
            
            return {
                "directory": str(dir_path),
                "keyword": keyword,
                "results": results[:20]  # 限制返回20个结果
            }
        except Exception as e:
            return {"error": f"搜索失败:{str(e)}"}
    
    async def list_directory(self, path: str) -> dict:
        """列出目录内容"""
        if not self._is_path_allowed(path):
            return {"error": f"访问被拒绝:{path}不在允许的目录中"}
        
        try:
            dir_path = Path(path)
            if not dir_path.is_dir():
                return {"error": f"不是有效目录:{path}"}
            
            items = []
            for item in sorted(dir_path.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "path": str(dir_path),
                "items": items
            }
        except Exception as e:
            return {"error": f"列表失败:{str(e)}"}

    async def handle_request(self, request: dict) -> dict:
        """处理MCP请求"""
        method = request.get("method")
        params = request.get("params", {})
        
        # 列出可用工具
        if method == "tools/list":
            return {
                "tools": [
                    {"name": name, **info}
                    for name, info in self.tools.items()
                ]
            }
        
        # 调用工具
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "read_file":
                return await self.read_file(**tool_args)
            elif tool_name == "search_files":
                return await self.search_files(**tool_args)
            elif tool_name == "list_directory":
                return await self.list_directory(**tool_args)
            else:
                return {"error": f"未知工具:{tool_name}"}
        
        return {"error": f"未知方法:{method}"}
    
    async def run(self):
        """启动服务器(标准输入输出通信)"""
        print("MCP文件系统服务器已启动", flush=False)
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, input
                )
                request = json.loads(line)
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except EOFError:
                break
            except Exception as e:
                error_response = {"error": str(e)}
                print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    import sys
    # 从命令行参数获取允许的目录
    if len(sys.argv) < 2:
        print("Usage: python filesystem_server.py <allowed_dir1> [allowed_dir2 ...]")
        sys.exit(1)
    
    allowed_dirs = sys.argv[1:]
    server = FilesystemMCPServer(allowed_directories=allowed_dirs)
    asyncio.run(server.run())
    