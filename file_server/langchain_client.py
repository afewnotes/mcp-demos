from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
import subprocess
import json
import os
import sys

class MCPFilesystemClient:
    """MCP文件系统客户端"""
    
    def __init__(self, server_script: str, allowed_dirs: list[str]):
        """初始化客户端
        
        Args:
            server_script: MCP服务器脚本路径
            allowed_dirs: 允许访问的目录
        """
        # 启动MCP服务器子进程
        self.process = subprocess.Popen(
            [sys.executable, server_script, *allowed_dirs],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        
        # 读取启动消息
        startup_line = self.process.stdout.readline()
        if "MCP文件系统服务器已启动" not in startup_line:
            raise RuntimeError(f"MCP服务器启动失败: {startup_line}")

        self.tools = self._create_tools()
    
    def _call_mcp_tool(self, tool_name: str, **kwargs) -> str:
        """调用MCP工具"""
        request = {
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": kwargs}
        }
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        response = json.loads(self.process.stdout.readline())
        return json.dumps(response, ensure_ascii=False, indent=2)
    
    def _create_tools(self) -> list:
        """创建LangChain工具"""
        return [
            Tool(
                name="read_file",
                func=lambda path: self._call_mcp_tool("read_file", path=path),
                description="读取文件内容。参数:path(文件路径)"
            ),
            Tool(
                name="search_files",
                func=lambda directory, keyword: self._call_mcp_tool(
                    "search_files", directory=directory, keyword=keyword
                ),
                description="搜索包含关键词的文件。参数:directory(目录),keyword(关键词)"
            ),
            Tool(
                name="list_directory",
                func=lambda path: self._call_mcp_tool("list_directory", path=path),
                description="列出目录内容。参数:path(目录路径)"
            )
        ]
    
    def create_agent(self) -> AgentExecutor:
        """创建LangChain Agent"""
        llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model="deepseek-ai/DeepSeek-V3", temperature=0.7
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个文件系统助手,可以帮助用户读取、搜索和浏览文件。"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)