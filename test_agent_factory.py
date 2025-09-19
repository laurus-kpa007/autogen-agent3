import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.agent_builder import create_orchestrator_agent
from orchestrator.agent_factory import AgentFactory

async def test_agent_factory():
    """에이전트 팩토리 테스트"""
    print("Agent Factory Test Start")
    print("-" * 50)

    try:
        # 에이전트 생성
        print("1. Creating agent...")
        agent = await create_orchestrator_agent()

        # 에이전트 정보 확인
        agent_info = AgentFactory.get_agent_type_info(agent)
        print(f"2. Agent info: {agent_info}")

        # 간단한 테스트 실행
        print("3. Running simple test...")

        if hasattr(agent, 'run'):
            # 기본 인사 테스트
            response = await agent.run(task="Hello!")
            if hasattr(response, 'chat_message'):
                # PromptBasedAgent의 Response
                print(f"Response: {response.chat_message.content if response.chat_message else 'No response'}")
            elif hasattr(response, 'messages'):
                # AssistantAgent의 TaskResult
                print(f"Response: {response.messages[-1].content if response.messages else 'No response'}")
            else:
                print(f"Response type: {type(response)}")
        else:
            print("No run method available.")

        print("Test completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_factory())