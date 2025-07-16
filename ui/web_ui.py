import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import Response
from autogen_core import CancellationToken
from orchestrator.llm_connector import get_llm_client
from orchestrator.mcp_tool_loader import load_mcp_tools

# TrackableAssistantAgent: 메시지를 Streamlit UI로 전달하도록 확장
class TrackableAssistantAgent(AssistantAgent):
    async def on_messages_stream(self, messages, cancellation_token):
        async for evt in super().on_messages_stream(messages, cancellation_token):
            # Assistant의 텍스트 응답만 추가
            if isinstance(evt, TextMessage) and evt.source == "assistant":
                st.session_state.history.append(("assistant", evt.content))
            elif isinstance(evt, Response) and hasattr(evt, "chat_message"):
                msg = evt.chat_message
                if isinstance(msg, TextMessage) and msg.source == "assistant":
                    st.session_state.history.append(("assistant", msg.content))
            yield evt

async def init_agent():
    llm = get_llm_client()
    tools = await load_mcp_tools()
    return TrackableAssistantAgent(
        name="orch",
        model_client=llm,
        tools=tools,
        system_message="당신은 오케스트레이터입니다. 질문을 분석하고 필요하면 MCP 도구를 사용하거나 LLM으로 직접 답변하세요.",
        reflect_on_tool_use=True,
        model_client_stream=True
    )

def run():
    st.title("🔗 AutoGen MCP Orchestrator Chatbot")

    if "agent" not in st.session_state:
        st.session_state.history = []
        st.session_state.agent = asyncio.new_event_loop().run_until_complete(init_agent())

    # 사용자 입력 UI
    st.text_input("질문을 입력하세요:", key="user_input")
    if st.button("전송"):
        user_input = st.session_state.user_input
        st.session_state.history.append(("user", user_input))
        st.session_state.user_input = ""

        async def ask():
            async for _ in st.session_state.agent.on_messages_stream(
                [TextMessage(content=user_input, source="user")],
                CancellationToken()
            ):
                pass

        asyncio.new_event_loop().run_until_complete(ask())

    # 메시지 렌더링
    for role, msg in st.session_state.history:
        if role == "user":
            st.markdown(f"**🧑  {msg}**")
        else:
            st.markdown(f"**🤖  {msg}**")
