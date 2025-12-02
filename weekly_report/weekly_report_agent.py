
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.prompts import ChatPromptTemplate
from datetime import datetime, timedelta
from mcp_manager import MCPManager
from tool_router import ToolRouter
import os

class WeeklyReportAgent:
    """周报自动生成Agent"""
    
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
        self.router = ToolRouter(mcp_manager)
        self.llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model="deepseek-ai/DeepSeek-V3", temperature=0
        )
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """创建Agent"""
        tools = self.router.create_langchain_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个高效的工作助手,专门生成周报。

任务流程:
1. 使用 query_database 查询本周的关键数据(销售额、订单量等)
2. 使用 search_knowledge 查找相关的项目文档和会议记录
3. 使用 read_file 读取上周的工作计划
4. 综合以上信息,生成结构化的周报
5. 使用 write_file 保存周报到指定路径

周报格式要求:
- 本周工作总结(3-5条)
- 关键数据指标(表格形式)
- 遇到的问题及解决方案
- 下周工作计划

注意:确保数据准确,表述简洁专业。"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    def generate_report(self, output_path: str = "weekly_report.md") -> str:
        """生成周报"""
        # 计算本周时间范围
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        task = f"""
请生成 {week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')} 的周报。

具体要求:
1. 查询数据库获取本周销售数据
2. 搜索知识库中本周的会议记录
3. 生成周报并保存到 {output_path}

请按照系统提示的格式生成专业的周报。
"""
        
        result = self.agent.invoke({"input": task})
        return result['output']