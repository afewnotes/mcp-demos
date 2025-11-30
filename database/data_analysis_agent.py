
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.tools import StructuredTool
import asyncio
import os

class DataAnalysisAgent:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model="deepseek-ai/DeepSeek-V3", temperature=0
        )
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """从MCP服务器创建LangChain工具"""
        tools = []
        
        # 执行查询工具
        tools.append(StructuredTool.from_function(
            coroutine=lambda sql, limit=100: self.mcp_client.call_tool("execute_query", {"sql": sql, "limit": limit}),
            func=lambda sql, limit=100: asyncio.run(
                self.mcp_client.call_tool("execute_query", {"sql": sql, "limit": limit})
            ),
            name="execute_query",
            description="执行SQL查询并返回结果(仅支持SELECT)"
        ))
        
        # 获取表结构工具
        tools.append(StructuredTool.from_function(
            coroutine=lambda table_name: self.mcp_client.call_tool("get_table_schema", {"table_name": table_name}),
            func=lambda table_name: asyncio.run(
                self.mcp_client.call_tool("get_table_schema", {"table_name": table_name})
            ),
            name="get_table_schema",
            description="获取表的列名和数据类型"
        ))
        
        # 列出所有表工具
        tools.append(StructuredTool.from_function(
            coroutine=lambda: self.mcp_client.call_tool("list_tables", {}),
            func=lambda: asyncio.run(
                self.mcp_client.call_tool("list_tables", {})
            ),
            name="list_tables",
            description="列出数据库中所有表名"
        ))
        
        return tools
    
    def _create_agent(self):
        """创建Agent"""
        tools = self._create_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个数据分析专家。用户会用自然语言提问,你需要:
1. 使用list_tables了解有哪些表
2. 使用get_table_schema了解表结构
3. 编写SQL查询获取数据
4. 分析数据并用通俗语言解释结果

注意:只能使用SELECT查询,不能修改数据。"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    async def analyze(self, question: str) -> str:
        """分析数据并回答问题"""
        result = await self.agent.ainvoke({"input": question})
        return result['output']