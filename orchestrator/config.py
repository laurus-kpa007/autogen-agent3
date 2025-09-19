# LLM 설정
LLM_CONFIG = {
    "base_url": "http://127.0.0.1:1234/v1",
    "model": "gemma-3-4b-it",
    "api_key": "",
}

# MCP 툴 서버 설정 (필요시 환경변수 또는 DB 연동 가능)
MCP_SERVERS = [
    # {
    #     "type": "sse",
    #     "url": "http://192.168.0.23:8000/sse"   # 또는 "/streamable-http" 등 엔드포인트
    # }
    # {
    #     "type": "stdio",
    #     "command": "npx",
    #     "args": ["-y", "@isnow890/naver-search-mcp"],
    #     "env": {
    #         "NAVER_CLIENT_ID": "URveH8D_D7bOOCzG5YXm",
    #         "NAVER_CLIENT_SECRET": "O0mj4SkKYS"
    #     }
    # }
    {
        "type": "stdio",
        "command": "D:\\Python\\AutoGen_MCP\\mcp-resource-monitor\\venv\\Scripts\\python.exe",
        "args": ["D:\\Python\\AutoGen_MCP\\mcp-resource-monitor\\app\\main.py"]
    }
    # {
    #     "type": "stdio",
    #     "command": "C:\\Users\\lauru\\PythonProjects\\AutoGen_MCP\\mcp-weather\\venv\\Scripts\\python.exe",
    #     "args": ["C:\\U/sers\\lauru\\PythonProjects\\AutoGen_MCP\\mcp-weather\\server.py"]
    # }
]
