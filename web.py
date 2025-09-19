import gradio as gr
import asyncio
from orchestrator.agent_builder import create_orchestrator_agent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_agentchat.messages import ToolCallRequestEvent, ToolCallExecutionEvent

async def init_agent():
    return await create_orchestrator_agent()

def sync_init():
    return asyncio.new_event_loop().run_until_complete(init_agent())

def chat_fn(user_message, history):
    if not hasattr(chat_fn, "agent"):
        chat_fn.agent = sync_init()

    history = history or []
    history.append({"role": "user", "content": user_message})

    # 단계별 메시지 기록
    assistant_msgs = []

    # 전체 실행 (툴 호출 / 추론)
    loop = asyncio.new_event_loop()
    async def run_full():
        async for evt in chat_fn.agent.on_messages_stream(
            [TextMessage(content=user_message, source="user")],
            CancellationToken()
        ):
            # 툴 호출 요청 로그
            if isinstance(evt, ToolCallRequestEvent):
                assistant_msgs.append({
                    "role": "assistant",
                    "content": f"🛠 calling tool: {evt.name}({evt.arguments})",
                    "metadata": {"title": f"Tool 호출: {evt.name}"}
                })
            elif isinstance(evt, ToolCallExecutionEvent):
                assistant_msgs.append({
                    "role": "assistant",
                    "content": f"✅ tool {evt.name} 실행 결과: {evt.result}",
                    "metadata": {"title": f"Tool 결과: {evt.name}"}
                })
            # 최종 LLM 응답
            elif hasattr(evt, "content"):
                assistant_msgs.append({
                    "role": "assistant",
                    "content": evt.content,
                    "metadata": {"title": "최종 요약"}
                })
    loop.run_until_complete(run_full())

    # history 확장 후 반환
    return history + assistant_msgs

demo = gr.ChatInterface(
    fn=chat_fn,
    type="messages",
    title="AutoGen Orchestrator (과정 보기)",
    description="질문 입력 시 툴 호출 및 마지막 응답 과정을 단계별로 보여줍니다."
)

if __name__ == "__main__":
    demo.launch()
