
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import psycopg2
from data_analysis_agent import DataAnalysisAgent
import os

async def run_demo():
    """运行数据分析演示"""
    
    # 1. 启动MCP服务器
    server_params = StdioServerParameters(
        command="python",
        args=["database_mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 2. 创建分析Agent
            agent = DataAnalysisAgent(session)
            
            # 3. 业务问题示例
            questions = [
                "数据库里有哪些表?",
                "统计每个月的订单总金额",
                "找出销售额最高的前5个产品",
                "分析不同地区的客户分布"
            ]
            
            for question in questions:
                print(f"\n{'='*60}")
                print(f"问题: {question}")
                print(f"{'='*60}")
                
                answer = await agent.analyze(question)
                print(f"\n回答:\n{answer}\n")

# 运行演示
if __name__ == "__main__":
    # 准备测试数据库
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        database='sales_db',
        user='postgres',
        password='123456'
    )
    cursor = conn.cursor()
    
    # 创建示例表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            product_name VARCHAR(100),
            amount DECIMAL(10,2),
            region VARCHAR(50),
            order_date DATE
        )
    """)
    
    # 插入示例数据
    cursor.execute("""
        INSERT INTO orders (product_name, amount, region, order_date) VALUES
        ('笔记本电脑', 5999.00, '华东', '2024-01-15'),
        ('机械键盘', 399.00, '华南', '2024-01-16'),
        ('显示器', 1299.00, '华北', '2024-02-20'),
        ('鼠标', 99.00, '华东', '2024-02-21')
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # 运行Agent
    asyncio.run(run_demo())