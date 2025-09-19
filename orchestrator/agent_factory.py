from typing import Union, List, Any
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelInfo
from .prompt_agent import PromptBasedAgent
from .tool_parser import ToolCallParser

class AgentFactory:
    """LLM 특성에 따라 적절한 에이전트를 생성하는 팩토리 클래스"""

    @staticmethod
    def detect_function_calling_support(model_client) -> bool:
        """LLM이 function calling을 지원하는지 감지"""
        try:
            # ModelInfo에서 function_calling 지원 여부 확인
            if hasattr(model_client, 'model_info'):
                model_info = model_client.model_info

                if hasattr(model_info, 'function_calling'):
                    return model_info.function_calling
                elif isinstance(model_info, dict):
                    return model_info.get('function_calling', False)

            # model_client 직접 확인
            if hasattr(model_client, '_function_calling'):
                return model_client._function_calling

            # 설정에서 확인
            if hasattr(model_client, 'parallel_tool_calls'):
                return model_client.parallel_tool_calls

            # 기본값: function calling 미지원으로 간주
            return False

        except Exception as e:
            print(f"Function calling support detection error: {str(e)}")
            # 오류 발생시 안전하게 미지원으로 처리
            return False

    @staticmethod
    async def create_agent(
        model_client,
        tools: List[Any],
        system_message: str,
        max_tool_iterations: int = 5,
        **kwargs
    ) -> Union[AssistantAgent, PromptBasedAgent]:
        """
        LLM 특성에 따라 적절한 에이전트 생성

        Args:
            model_client: LLM 클라이언트
            tools: 사용할 도구 목록
            system_message: 시스템 메시지
            max_tool_iterations: 최대 도구 호출 반복 횟수
            **kwargs: AssistantAgent에 전달할 추가 인수

        Returns:
            AssistantAgent 또는 PromptBasedAgent
        """

        # Function calling 지원 여부 확인
        supports_function_calling = AgentFactory.detect_function_calling_support(model_client)

        print(f"Function calling support: {supports_function_calling}")

        if supports_function_calling and tools:
            # Function calling 지원하는 경우 - 기존 AssistantAgent 사용
            print("Using AssistantAgent (Function calling supported)")

            return AssistantAgent(
                name=kwargs.get("name", "orchestrator"),
                model_client=model_client,
                tools=tools,
                system_message=system_message,
                reflect_on_tool_use=kwargs.get("reflect_on_tool_use", True),
                model_client_stream=kwargs.get("model_client_stream", True),
                max_tool_iterations=max_tool_iterations,
            )

        else:
            # Function calling 미지원하거나 도구가 없는 경우 - 프롬프트 기반 에이전트 사용
            reason = "Function calling not supported" if not supports_function_calling else "No tools"
            print(f"Using PromptBasedAgent ({reason})")

            # 프롬프트 기반 에이전트용 시스템 메시지 생성
            if tools:
                enhanced_system_message = ToolCallParser.create_system_prompt(tools)
            else:
                enhanced_system_message = system_message

            return PromptBasedAgent(
                model_client=model_client,
                tools=tools,
                system_message=enhanced_system_message,
                max_tool_iterations=max_tool_iterations
            )

    @staticmethod
    def get_agent_type_info(agent) -> dict:
        """에이전트 타입과 정보 반환 (디버깅용)"""
        if isinstance(agent, AssistantAgent):
            return {
                "type": "AssistantAgent",
                "function_calling": True,
                "tools_count": len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0
            }
        elif isinstance(agent, PromptBasedAgent):
            return {
                "type": "PromptBasedAgent",
                "function_calling": False,
                "tools_count": len(agent.tools) if agent.tools else 0
            }
        else:
            return {
                "type": type(agent).__name__,
                "function_calling": None,
                "tools_count": None
            }