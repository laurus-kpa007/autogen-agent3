import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolCall:
    """툴 호출 정보를 담는 데이터클래스"""
    name: str
    arguments: Dict[str, Any]

class ToolCallParser:
    """LLM 응답에서 툴 호출을 파싱하고 포맷팅하는 클래스"""

    @staticmethod
    def parse_tool_calls(response: str) -> List[ToolCall]:
        """응답에서 툴 호출을 추출"""
        tool_calls = []

        # XML 스타일 툴 호출 패턴 매칭
        pattern = r'<tool_call>\s*<name>(.*?)</name>\s*<arguments>(.*?)</arguments>\s*</tool_call>'
        matches = re.findall(pattern, response, re.DOTALL)

        for name, args_str in matches:
            try:
                name = name.strip()
                args_str = args_str.strip()

                # JSON 파싱 시도
                try:
                    arguments = json.loads(args_str)
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 빈 딕셔너리로 처리
                    arguments = {}

                tool_calls.append(ToolCall(name=name, arguments=arguments))
            except Exception as e:
                print(f"툴 호출 파싱 오류: {e}")
                continue

        return tool_calls

    @staticmethod
    def format_tool_result(tool_name: str, result: Any) -> str:
        """툴 실행 결과를 포맷팅"""
        return f"\n<tool_result name='{tool_name}'>\n{str(result)}\n</tool_result>\n"

    @staticmethod
    def create_system_prompt(tools: List[Any]) -> str:
        """사용 가능한 툴들의 시스템 프롬프트 생성"""
        if not tools:
            return (
                "당신은 오케스트레이터 AI입니다. 사용자 질문을 분석하고 "
                "직접 답변하세요. 답변은 항상 질문과 동일한 언어로 하십시오."
            )

        tool_descriptions = []
        for tool in tools:
            desc = f"- {tool.name}: {tool.description if hasattr(tool, 'description') else '도구 설명 없음'}"

            # 입력 스키마가 있으면 추가
            if hasattr(tool, 'input_schema') and tool.input_schema:
                schema = tool.input_schema
                if isinstance(schema, dict) and 'properties' in schema:
                    params = []
                    for param_name, param_info in schema['properties'].items():
                        param_type = param_info.get('type', 'any')
                        param_desc = param_info.get('description', '')
                        params.append(f"{param_name}({param_type}): {param_desc}")
                    if params:
                        desc += f"\n  매개변수: {', '.join(params)}"

            tool_descriptions.append(desc)

        tools_text = "\n".join(tool_descriptions)

        return f"""당신은 오케스트레이터 AI입니다. 사용자 질문을 분석하고 필요시 도구를 사용하거나 직접 답변하세요.

사용 가능한 도구:
{tools_text}

도구 호출 형식:
<tool_call>
<name>도구명</name>
<arguments>{{"param": "value"}}</arguments>
</tool_call>

규칙:
1. 도구가 필요한 경우에만 호출하세요
2. 정확한 JSON 형식의 인수를 사용하세요
3. 도구 호출 후 결과를 바탕으로 최종 답변을 제공하세요
4. 답변은 항상 질문과 동일한 언어로 하십시오
5. 도구 호출이 불필요한 경우 직접 답변하세요"""

    @staticmethod
    def remove_tool_calls_from_response(response: str) -> str:
        """응답에서 툴 호출 부분을 제거하고 순수 텍스트만 반환"""
        # 툴 호출 패턴 제거
        pattern = r'<tool_call>.*?</tool_call>'
        cleaned = re.sub(pattern, '', response, flags=re.DOTALL)

        # 툴 결과 패턴 제거
        pattern = r'<tool_result.*?>.*?</tool_result>'
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)

        # 여러 개의 연속된 공백/줄바꿈을 정리
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)

        return cleaned.strip()