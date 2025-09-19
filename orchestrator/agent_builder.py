import asyncio
from orchestrator.llm_connector import get_llm_client
from orchestrator.mcp_tool_loader import load_mcp_tools
from orchestrator.agent_factory import AgentFactory

async def create_orchestrator_agent():
    """
    LLM 특성에 따라 적절한 에이전트를 생성
    - Function calling 지원: AssistantAgent 사용
    - Function calling 미지원: PromptBasedAgent 사용
    """
    llm_client = get_llm_client()
    tools = await load_mcp_tools()

    system_prompt = (
        "당신은 오케스트레이터 AI입니다. 사용자 질문을 분석하고 "
        "필요 시 MCP 도구를 사용하거나 LLM을 통해 직접 답변하세요. "
        "답변은 항상 질문과 동일한 언어로 하십시오."
    )

    # AgentFactory를 사용해서 적절한 에이전트 생성
    agent = await AgentFactory.create_agent(
        model_client=llm_client,
        tools=tools,
        system_message=system_prompt,
        max_tool_iterations=5,
        name="orchestrator",
        reflect_on_tool_use=True,
        model_client_stream=True
    )

    # 에이전트 정보 출력 (디버깅용)
    agent_info = AgentFactory.get_agent_type_info(agent)
    print(f"Agent created: {agent_info}")

    return agent
