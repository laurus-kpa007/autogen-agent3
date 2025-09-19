import asyncio
from typing import List, Any, AsyncGenerator, Dict, Optional
from autogen_agentchat.messages import TextMessage, ChatMessage
from autogen_core import CancellationToken
from autogen_agentchat.base import Response
from .tool_parser import ToolCallParser, ToolCall

class PromptBasedAgent:
    """프롬프트 기반으로 툴 호출을 처리하는 커스텀 에이전트"""

    def __init__(self, model_client, tools: List[Any], system_message: str, max_tool_iterations: int = 5):
        self.model_client = model_client
        self.tools = {tool.name: tool for tool in tools} if tools else {}
        self.system_message = system_message
        self.max_tool_iterations = max_tool_iterations
        self.conversation_history = []

    async def run(self, task: str) -> Response:
        """기본 실행 메서드 (AutoGen 호환성)"""
        messages = []
        async for message in self.run_stream(task=task):
            messages.append(message)

        # 마지막 메시지를 chat_message로, 나머지를 inner_messages로 사용
        if messages:
            return Response(chat_message=messages[-1], inner_messages=messages[:-1] if len(messages) > 1 else None)
        else:
            # 빈 응답의 경우
            empty_message = TextMessage(content="No response generated.", source="assistant")
            return Response(chat_message=empty_message)

    async def run_stream(self, task: str) -> AsyncGenerator[ChatMessage, None]:
        """스트리밍 방식으로 응답 생성"""
        input_message = TextMessage(content=task, source="user")
        async for message in self.on_messages_stream([input_message], CancellationToken()):
            yield message

    async def on_messages_stream(self, messages: List[ChatMessage], cancellation_token: CancellationToken) -> AsyncGenerator[ChatMessage, None]:
        """메시지 스트림 처리 (AutoGen 호환 인터페이스)"""
        # 새로운 메시지를 대화 히스토리에 추가
        for msg in messages:
            if hasattr(msg, 'content') and hasattr(msg, 'source'):
                self.conversation_history.append({"role": msg.source, "content": msg.content})

        # 시스템 프롬프트 포함한 전체 대화 구성
        full_conversation = [{"role": "system", "content": self.system_message}]
        full_conversation.extend(self.conversation_history)

        # 툴 호출 반복 처리
        iteration = 0
        while iteration < self.max_tool_iterations:
            if cancellation_token.is_cancelled():
                break

            # LLM 호출
            try:
                response = await self._call_llm(full_conversation)
                if not response:
                    break

                # 툴 호출 파싱
                tool_calls = ToolCallParser.parse_tool_calls(response)

                if not tool_calls:
                    # 툴 호출이 없으면 최종 응답으로 처리
                    clean_response = ToolCallParser.remove_tool_calls_from_response(response)
                    if clean_response.strip():
                        yield TextMessage(content=clean_response, source="assistant")
                    break

                # 툴 호출 실행
                tool_results = []
                for tool_call in tool_calls:
                    try:
                        result = await self._execute_tool(tool_call)
                        tool_results.append(ToolCallParser.format_tool_result(tool_call.name, result))

                        # 툴 실행 상태를 스트리밍
                        status_msg = f"🛠 도구 '{tool_call.name}' 실행 완료"
                        yield TextMessage(content=status_msg, source="assistant")

                    except Exception as e:
                        error_result = f"오류: {str(e)}"
                        tool_results.append(ToolCallParser.format_tool_result(tool_call.name, error_result))

                # 툴 결과를 대화에 추가
                if tool_results:
                    tool_response = response + "\n" + "\n".join(tool_results)
                    full_conversation.append({"role": "assistant", "content": tool_response})

                iteration += 1

            except Exception as e:
                error_msg = f"LLM 호출 오류: {str(e)}"
                yield TextMessage(content=error_msg, source="assistant")
                break

        # 마지막 대화를 히스토리에 저장
        if full_conversation and len(full_conversation) > len(self.conversation_history) + 1:
            self.conversation_history.append({
                "role": "assistant",
                "content": full_conversation[-1]["content"]
            })

    async def _call_llm(self, conversation: List[Dict[str, str]]) -> str:
        """LLM 호출 - 직접 HTTP API 사용"""
        try:
            import httpx
            import json
            from orchestrator.config import LLM_CONFIG

            # 대화 형식 변환
            api_messages = []
            for msg in conversation:
                api_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # HTTP API 직접 호출
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{LLM_CONFIG['base_url']}/chat/completions",
                    json={
                        "model": LLM_CONFIG["model"],
                        "messages": api_messages,
                        "stream": False,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    headers={"Authorization": f"Bearer {LLM_CONFIG['api_key']}"} if LLM_CONFIG['api_key'] else {},
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        return content.strip() if content else "응답을 생성할 수 없습니다."
                    else:
                        return "LLM 응답 형식이 올바르지 않습니다."
                else:
                    print(f"LLM API 오류: {response.status_code} - {response.text}")
                    return "안녕하세요! 무엇을 도와드릴까요?"

        except Exception as e:
            print(f"LLM 호출 실패: {e}")
            return "안녕하세요! 무엇을 도와드릴까요?"

    async def _execute_tool(self, tool_call: ToolCall) -> Any:
        """툴 실행"""
        if tool_call.name not in self.tools:
            raise ValueError(f"알 수 없는 도구: {tool_call.name}")

        tool = self.tools[tool_call.name]

        try:
            # MCP 툴 실행
            if hasattr(tool, 'call'):
                # 비동기 호출
                if asyncio.iscoroutinefunction(tool.call):
                    result = await tool.call(tool_call.arguments)
                else:
                    result = tool.call(tool_call.arguments)
            else:
                # 다른 형태의 툴 인터페이스 처리
                result = await tool(tool_call.arguments)

            return result

        except Exception as e:
            raise Exception(f"도구 '{tool_call.name}' 실행 실패: {str(e)}")

    def reset_conversation(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []