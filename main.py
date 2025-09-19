import warnings
warnings.filterwarnings(
    "ignore",
    message="^Resolved model mismatch:",
    category=UserWarning
)
import logging
from autogen_core import TRACE_LOGGER_NAME, EVENT_LOGGER_NAME

# 기본 로거 메시지는 경고 이상으로 설정
logging.basicConfig(level=logging.WARNING)

# Trace 로그 완전 비활성화
logging.getLogger(TRACE_LOGGER_NAME).setLevel(logging.ERROR)

# 구조화된 이벤트 로그 비활성화
logging.getLogger(EVENT_LOGGER_NAME).setLevel(logging.ERROR)

import sys

def main():
    print("모드를 선택하세요:")
    print("1) CLI")
    print("2) Web UI")
    mode = input("> ")

    if mode.strip() == "1":
        import asyncio
        from orchestrator.agent_builder import create_orchestrator_agent
        from autogen_agentchat.ui import Console
        from autogen_agentchat.agents import AssistantAgent

        async def run_cli():
            agent = await create_orchestrator_agent()
            print("질문을 입력하세요 ('exit' 입력 시 종료):")

            # 에이전트 타입 확인
            from orchestrator.prompt_agent import PromptBasedAgent
            is_prompt_based = isinstance(agent, PromptBasedAgent)

            while True:
                query = input("User: ")
                if query.lower() in ("exit", "quit"):
                    break

                if is_prompt_based:
                    # PromptBasedAgent용 처리
                    try:
                        response = await agent.run(task=query)
                        if hasattr(response, 'chat_message') and response.chat_message:
                            print("Assistant:", response.chat_message.content)
                        else:
                            print("Assistant: 응답을 생성할 수 없습니다.")
                    except Exception as e:
                        print(f"Assistant: 오류가 발생했습니다: {e}")
                else:
                    # AssistantAgent용 처리 (기존 방식)
                    try:
                        await Console(agent.run_stream(task=query), output_stats=False)
                    except Exception as e:
                        print(f"Assistant: 오류가 발생했습니다: {e}")

                print()
        asyncio.run(run_cli())

    elif mode.strip() == "2":
        import streamlit.web.cli as stcli
        import os
        import sys
        from ui import web_ui
        sys.argv = ["streamlit", "run", "ui/web_ui.py"]
        sys.exit(stcli.main())

if __name__ == "__main__":
    main()
