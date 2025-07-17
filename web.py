import gradio as gr
import asyncio
from orchestrator.agent_builder import create_orchestrator_agent
from autogen_agentchat.messages import TextMessage

# Orchestrator 에이전트 초기화 (싱크 래퍼)
async def init_agent():
    return await create_orchestrator_agent()

def sync_init():
    return asyncio.new_event_loop().run_until_complete(init_agent())

# Gradio용 챗 함수 (단일 응답 방식)
def chat_fn(user_message, history):
    if not hasattr(chat_fn, "agent"):
        chat_fn.agent = sync_init()
    # 에이전트에 질의 보내고 결과 가져오기
    result = asyncio.new_event_loop().run_until_complete(
        chat_fn.agent.run(task=user_message)
    )
    reply = result.messages[-1].content
    return reply

# Gradio UI 셋업
demo = gr.ChatInterface(
    fn=chat_fn,
    title="AutoGen Orchestrator Chatbot",
    description="질문을 입력하면 Orchestrator가 답변해 줍니다."
)

if __name__ == "__main__":
    demo.launch()
