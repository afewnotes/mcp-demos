
from langchain_classic.tools import StructuredTool
from typing import List
from mcp_manager import MCPManager

class ToolRouter:
    """智能工具路由器"""
    
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
    
    def create_langchain_tools(self) -> List[StructuredTool]:
        """将MCP工具转换为LangChain工具"""
        tools = []
        
        # 文件系统工具 - 读取文件
        async def read_file_async(path: str) -> str:
            result = await self.mcp_manager.call_tool("filesystem", "read_file", {"path": path})
            return str(result)
        
        tools.append(StructuredTool.from_function(
            func=lambda path: "",  # 占位符，实际不会被调用
            coroutine=read_file_async,
            name="read_file",
            description="读取指定路径的文件内容"
        ))
        
        # 文件系统工具 - 写入文件
        async def write_file_async(path: str, content: str) -> str:
            result = await self.mcp_manager.call_tool("filesystem", "write_file", 
                {"path": path, "content": content})
            return str(result)
        
        tools.append(StructuredTool.from_function(
            func=lambda path, content: "",  # 占位符
            coroutine=write_file_async,
            name="write_file",
            description="将内容写入指定文件"
        ))
        
        # 数据库工具
        async def query_database_async(sql: str) -> str:
            result = await self.mcp_manager.call_tool("database", "execute_query", {"sql": sql})
            return str(result)
        
        tools.append(StructuredTool.from_function(
            func=lambda sql: "",  # 占位符
            coroutine=query_database_async,
            name="query_database",
            description="执行SQL查询获取业务数据(仅支持SELECT)"
        ))
        
        # 知识库工具
        async def search_knowledge_async(query: str) -> str:
            result = await self.mcp_manager.call_tool("knowledge", "search", {"query": query})
            return str(result)
        
        tools.append(StructuredTool.from_function(
            func=lambda query: "",  # 占位符
            coroutine=search_knowledge_async,
            name="search_knowledge",
            description="在知识库中搜索相关文档"
        ))
        
        return tools