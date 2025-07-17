import asyncio
from autogen_agentchat.agents import AssistantAgent
from orchestrator.llm_connector import get_llm_client
from orchestrator.mcp_tool_loader import load_mcp_tools

async def create_orchestrator_agent():
    llm_client = get_llm_client()
    tools = await load_mcp_tools()

    system_prompt = (
        "당신은 오케스트레이터 AI입니다. 사용자 질문을 분석하고 "
        "필요 시 MCP 도구를 사용하거나 LLM을 통해 직접 답변하세요. "
        "답변은 항상 사용자 언어로 하십시오."
    )

    return AssistantAgent(
        name="orchestrator",
        model_client=llm_client,
        tools=tools,
        system_message=system_prompt,
        reflect_on_tool_use=True,
        # parallel_tool_calls=True,     # 동시에 여러 툴 호출 허용
        model_client_stream=True,
        max_tool_iterations=2,        # 최대 2회 툴 호출 루프 실행
    )
