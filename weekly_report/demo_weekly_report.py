
import asyncio
from mcp_manager import MCPManager
from weekly_report_agent import WeeklyReportAgent

async def main():
    """周报生成完整演示"""
    
    # 1. 初始化MCP管理器
    print("🚀 启动MCP服务器...")
    mcp_manager = MCPManager()
    await mcp_manager.connect_all()
    
    # 2. 显示可用工具
    print("\n📋 可用工具列表:")
    for tool in mcp_manager.get_all_tools():
        print(f"  - [{tool['server']}] {tool['name']}: {tool['description']}")
    
    # 3. 创建周报Agent
    print("\n🤖 创建周报生成Agent...")
    agent = WeeklyReportAgent(mcp_manager)
    
    try:
        # 4. 生成周报
        print("\n📝 开始生成周报...\n")
        result = agent.generate_report("reports/weekly_2024W48.md")
        
        print("\n✅ 周报生成完成!")
        print(f"\n{result}")
    finally:
        await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())