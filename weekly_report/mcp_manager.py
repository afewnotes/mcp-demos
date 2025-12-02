
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, List
import sys
from contextlib import AsyncExitStack

class MCPManager:
    """管理多个MCP服务器连接"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, List] = {}
        self.exit_stack = AsyncExitStack()
    
    async def connect_server(self, name: str, command: str, args: List[str]):
        """连接单个MCP服务器"""
        server_params = StdioServerParameters(
            command=command,
            args=args
        )
        
        # 启动服务器连接
        read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        
        self.sessions[name] = session
        
        # 获取该服务器提供的工具列表
        tools_response = await session.list_tools()
        self.tools[name] = tools_response.tools
        
        print(f"✅ 已连接 {name} MCP服务器,提供 {len(self.tools[name])} 个工具")

    async def cleanup(self):
        """关闭所有连接"""
        await self.exit_stack.aclose()
    
    async def connect_all(self):
        """连接所有MCP服务器"""
        # 1. 文件系统服务器
        await self.connect_server(
            name="filesystem",
            command=sys.executable,
            args=["../file_server/filesystem_server.py", "../file_server/test_files", "./"]
        )
        
        # 2. 数据库服务器
        await self.connect_server(
            name="database",
            command=sys.executable,
            args=["../database/database_mcp_server.py"]
        )
        
        # 3. 知识库服务器
        await self.connect_server(
            name="knowledge",
            command=sys.executable,
            args=["../knowledge/knowledge_mcp_server.py"]
        )
    
    async def call_tool(self, server_name: str, tool_name: str, args: dict):
        """调用指定服务器的工具"""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"服务器 {server_name} 未连接")
        
        result = await session.call_tool(tool_name, args)
        return result
    
    def get_all_tools(self) -> List[dict]:
        """获取所有可用工具列表"""
        all_tools = []
        for server_name, tools in self.tools.items():
            for tool in tools:
                all_tools.append({
                    'server': server_name,
                    'name': tool.name,
                    'description': tool.description
                })
        return all_tools