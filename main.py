import warnings
warnings.filterwarnings(
    "ignore",
    message="^Resolved model mismatch:",
    category=UserWarning
)

import sys

def main():
    print("모드를 선택하세요:")
    print("1) CLI")
    print("2) Web UI")
    mode = input("> ")

    if mode.strip() == "1":
        import asyncio
        from orchestrator.agent_builder import create_orchestrator_agent

        async def run_cli():
            agent = await create_orchestrator_agent()
            print("질문을 입력하세요 ('exit' 입력 시 종료):")
            while True:
                query = input("👤: ")
                if query.lower() in ("exit", "quit"):
                    break
                result = await agent.run(task=query)
                answer = result.messages[-1].content
                print("🤖:", answer)

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
