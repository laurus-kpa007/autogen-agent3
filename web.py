import gradio as gr
import asyncio
from orchestrator.agent_builder import create_orchestrator_agent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_agentchat.base import Response

async def init_agent():
    return await create_orchestrator_agent()

def sync_init():
    return asyncio.new_event_loop().run_until_complete(init_agent())

def chat_fn(message, history):
    if not hasattr(chat_fn, "agent"):
        chat_fn.agent = sync_init()
    last_content = ""
    async def process():
        nonlocal last_content
        async for evt in chat_fn.agent.on_messages_stream(
            [TextMessage(content=message, source="user")],
            CancellationToken()
        ):
            if isinstance(evt, Response):
                last_content = evt.chat_message.content
    asyncio.new_event_loop().run_until_complete(process())
    return last_content  # 문자열 하나만 리턴

demo = gr.ChatInterface(fn=chat_fn, title="AutoGen Chatbot", type="messages")
if __name__ == "__main__":
    demo.launch()
