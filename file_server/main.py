import asyncio
from filesystem_server import FilesystemMCPServer
from langchain_client import MCPFilesystemClient

# 测试1:直接测试MCP服务器
async def test_server():
    server = FilesystemMCPServer(allowed_directories=["./test_files"])
    
    # 测试读取文件
    result = await server.read_file("./test_files/sample.txt")
    print("读取文件:", result)
    
    # 测试搜索
    result = await server.search_files("./test_files", "python")
    print("搜索结果:", result)
    
    # 测试列表
    result = await server.list_directory("./test_files")
    print("目录列表:", result)

# 测试2:通过LangChain Agent使用
def test_agent():
    import os
    # 获取当前脚本所在目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "filesystem_server.py")
    
    client = MCPFilesystemClient(
        server_script=server_script,
        allowed_dirs=["./test_files"]
    )
    agent = client.create_agent()
    
    # 测试对话
    result = agent.invoke({
        "input": "请列出test_files目录的内容,然后读取第一个txt文件"
    })
    print("Agent回复:", result["output"])

if __name__ == "__main__":
    # 创建测试文件
    import os
    os.makedirs("./test_files", exist_ok=True)
    with open("./test_files/sample.txt", "w") as f:
        f.write("这是一个Python测试文件包含一些示例内容")
    
    # 运行测试
    print("=== 测试MCP服务器 ===")
    asyncio.run(test_server())
    
    print("=== 测试LangChain Agent ===")
    test_agent()