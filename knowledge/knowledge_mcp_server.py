
from mcp.server.fastmcp import FastMCP

# 创建一个名为 "knowledge" 的 MCP 服务器
mcp = FastMCP("knowledge")

@mcp.tool()
def search(query: str) -> str:
    """在知识库中搜索相关文档"""
    # 这里返回一些模拟数据
    return f"""
    找到关于 "{query}" 的相关文档:
    
    1. [会议记录] 2024-11-25 周会
       - 讨论了 Q4 销售目标
       - 确定了新产品发布日期
       
    2. [项目文档] API 接口规范 v2.0
       - 更新了用户认证接口
       - 新增了数据导出功能
       
    3. [技术方案] 数据库迁移指南
       - 详细描述了从 MySQL 迁移到 PostgreSQL 的步骤
    """

if __name__ == "__main__":
    mcp.run()
