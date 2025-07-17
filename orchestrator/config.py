# LLM 설정
LLM_CONFIG = {
    "base_url": "http://192.168.0.23:2345/v1",
    "model": "GPT-3.5 turbo",
    "api_key": "vLLM",
}

# MCP 툴 서버 설정 (필요시 환경변수 또는 DB 연동 가능)
MCP_SERVERS = [
    {
        "type": "stdio",
        "command": "C:\\Users\\lauru\\PythonProjects\\AutoGen_MCP\\mcp-resource-monitor\\venv\\Scripts\\python.exe",
        "args": ["C:\\Users\\lauru\\PythonProjects\\AutoGen_MCP\\mcp-resource-monitor\\app\\main.py"]
    }
    # {
    #     "type": "stdio",
    #     "command": "C:\\Users\\lauru\\PythonProjects\\AutoGen_MCP\\mcp-weather\\venv\\Scripts\\python.exe",
    #     "args": ["C:\\Users\\lauru\\PythonProjects\\AutoGen_MCP\\mcp-weather\\server.py"]
    # }
]
