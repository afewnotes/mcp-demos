import asyncio
import json
import sys
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
import psycopg2
from psycopg2.extras import RealDictCursor
from sql_safety import SQLSafetyChecker

class DatabaseMCPServer:
    def __init__(self, db_config: dict):
        self.server = Server("database-mcp-server")
        self.db_config = db_config
        self._register_handlers()
    
    def _get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def _is_safe_query(self, sql: str) -> bool:
        """SQL安全检查 - 使用SQLSafetyChecker"""
        is_safe, msg = SQLSafetyChecker.check(sql)
        if not is_safe:
            print(f"SQL安全检查失败: {msg}", file=sys.stderr)
        return is_safe
    
    def _register_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="execute_query",
                    description="执行SQL查询(仅支持SELECT)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL查询语句"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "限制返回行数(默认100)",
                                "default": 100
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                Tool(
                    name="get_table_schema",
                    description="获取表结构信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "表名"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="list_tables",
                    description="列出所有表名",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            if name == "execute_query":
                return await self._execute_query(
                    arguments.get("sql"),
                    arguments.get("limit", 100)
                )
            elif name == "get_table_schema":
                return await self._get_table_schema(arguments.get("table_name"))
            elif name == "list_tables":
                return await self._list_tables()
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _execute_query(self, sql: str, limit: int) -> Sequence[TextContent]:
        """执行SQL查询"""
        # 安全检查
        if not self._is_safe_query(sql):
            return [TextContent(
                type="text",
                text="❌ 安全检查失败:只允许SELECT查询"
            )]
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 添加LIMIT限制
            if 'LIMIT' not in sql.upper():
                sql = f"{sql} LIMIT {limit}"
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # 格式化结果
            result_text = f"✅ 查询成功,返回{len(results)}行:\n"
            result_text += json.dumps(results, indent=2, default=str)
            
            return [TextContent(type="text", text=result_text)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ 查询失败:{str(e)}"
            )]

    async def _get_table_schema(self, table_name: str) -> Sequence[TextContent]:
        """获取表结构"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 查询表结构
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not columns:
                return [TextContent(
                    type="text",
                    text=f"❌ 表 '{table_name}' 不存在"
                )]
            
            # 格式化输出
            schema_text = f"📊 表 '{table_name}' 结构:\n\n"
            for col in columns:
                schema_text += f"- {col['column_name']}: {col['data_type']}"
                if col['is_nullable'] == 'NO':
                    schema_text += " (NOT NULL)"
                schema_text += "\n"
            
            return [TextContent(type="text", text=schema_text)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ 获取表结构失败:{str(e)}"
            )]
    
    async def _list_tables(self) -> Sequence[TextContent]:
        """列出所有表"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            table_text = f"📋 数据库中有{len(tables)}个表:\n"
            table_text += "\n".join(f"- {table}" for table in tables)
            
            return [TextContent(type="text", text=table_text)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ 列出表失败:{str(e)}"
            )]

async def main():
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'sales_db',
        'user': 'postgres',
        'password': '123456'
    }
    
    server = DatabaseMCPServer(db_config)
    
    # 使用stdio传输
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())