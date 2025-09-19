import asyncio
from orchestrator.mcp_tool_loader import load_mcp_tools

async def debug_tools():
    """MCP 도구 목록 확인"""
    print("Loading MCP tools...")

    try:
        tools = await load_mcp_tools()
        print(f"\nFound {len(tools)} tools:")

        for i, tool in enumerate(tools):
            print(f"\n{i+1}. Tool Name: {tool.name}")
            print(f"   Description: {getattr(tool, 'description', 'No description')}")
            if hasattr(tool, 'input_schema'):
                print(f"   Input Schema: {tool.input_schema}")

    except Exception as e:
        print(f"Error loading tools: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tools())