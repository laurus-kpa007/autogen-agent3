import asyncio
from autogen_ext.tools.mcp import StdioServerParams, SseServerParams, mcp_server_tools
from orchestrator.config import MCP_SERVERS

async def load_mcp_tools():
    tools = []
    for conf in MCP_SERVERS:
        if conf["type"] == "stdio":
            params = StdioServerParams(
                command=conf["command"], 
                args=conf.get("args", []),
                env=conf.get("env", {}),
            )
        elif conf["type"] == "sse":
            params = SseServerParams(url=conf["url"], headers=conf.get("headers", {}))
        else:
            continue
        tools += await mcp_server_tools(params)
    return tools
