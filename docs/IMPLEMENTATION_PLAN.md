# 프롬프트 기반 툴 호출 시스템 구현 계획

## 1. 구현 순서

### Phase 1: 기본 구조 구현 (1-2일)

#### 1.1 ToolCallParser 클래스
```python
# orchestrator/tool_parser.py
class ToolCall:
    name: str
    arguments: dict

class ToolCallParser:
    @staticmethod
    def parse_tool_calls(response: str) -> List[ToolCall]

    @staticmethod
    def format_tool_result(tool_name: str, result: Any) -> str

    @staticmethod
    def create_system_prompt(tools: List[Tool]) -> str
```

#### 1.2 PromptBasedAgent 클래스
```python
# orchestrator/prompt_agent.py
class PromptBasedAgent:
    def __init__(self, model_client, tools, system_message)

    async def run_stream(self, task: str)

    async def on_messages_stream(self, messages, cancellation_token)

    def _execute_tool(self, tool_call: ToolCall) -> Any
```

### Phase 2: AgentFactory 구현 (1일)

#### 2.1 LLM 기능 감지
```python
# orchestrator/agent_factory.py
class AgentFactory:
    @staticmethod
    def detect_function_calling_support(model_client) -> bool

    @staticmethod
    async def create_agent(llm_client, tools, system_message)
```

#### 2.2 기존 코드 통합
- `agent_builder.py` 수정
- `llm_connector.py`에서 function_calling 설정 동적 변경

### Phase 3: 에러 처리 및 최적화 (1-2일)

#### 3.1 에러 처리
```python
class ToolExecutionError(Exception):
    pass

class PromptParsingError(Exception):
    pass
```

#### 3.2 스트리밍 지원
- 부분 응답 처리
- 툴 실행 상태 표시
- 취소 토큰 지원

### Phase 4: 테스트 및 검증 (1일)

## 2. 파일 구조

```
orchestrator/
├── agent_builder.py          # 수정: AgentFactory 사용
├── agent_factory.py          # 신규: 에이전트 팩토리
├── prompt_agent.py           # 신규: 프롬프트 기반 에이전트
├── tool_parser.py            # 신규: 툴 호출 파서
├── llm_connector.py          # 수정: 동적 function_calling 설정
├── mcp_tool_loader.py        # 기존 유지
└── config.py                 # 기존 유지

docs/
├── ARCHITECTURE.md           # 아키텍처 문서
├── IMPLEMENTATION_PLAN.md    # 구현 계획
└── USAGE_EXAMPLES.md         # 사용 예시

tests/
├── test_tool_parser.py       # 파서 테스트
├── test_prompt_agent.py      # 에이전트 테스트
└── test_integration.py       # 통합 테스트
```

## 3. 주요 설계 결정사항

### 3.1 프롬프트 형식
- XML 스타일 툴 호출: `<tool_call><name>...</name><arguments>...</arguments></tool_call>`
- JSON 인수 형식 사용
- 명확한 구분자로 파싱 안정성 확보

### 3.2 에이전트 선택 로직
```python
async def create_orchestrator_agent():
    llm_client = get_llm_client()
    tools = await load_mcp_tools()

    # function calling 지원 여부 확인
    if AgentFactory.detect_function_calling_support(llm_client):
        return AssistantAgent(...)  # 기존 방식
    else:
        return PromptBasedAgent(...)  # 새로운 방식
```

### 3.3 호환성 유지
- 기존 인터페이스 (`run_stream`, `on_messages_stream`) 유지
- 동일한 메시지 형식 반환
- 설정 변경 없이 자동 감지

## 4. 리스크 및 대응방안

### 4.1 프롬프트 파싱 실패
**리스크**: LLM이 정확한 형식으로 응답하지 않을 수 있음
**대응**:
- 재시도 로직 (최대 3회)
- 형식 오류시 예시 제공
- 폴백 모드 (툴 없이 일반 응답)

### 4.2 툴 실행 오류
**리스크**: MCP 서버 연결 실패, 인수 오류 등
**대응**:
- 상세한 에러 메시지 제공
- 툴별 재시도 정책
- 부분 실패시 계속 진행

### 4.3 성능 저하
**리스크**: 프롬프트 기반 처리로 인한 지연
**대응**:
- 툴 설명 캐싱
- 병렬 툴 실행
- 스트리밍으로 응답성 개선

## 5. 테스트 시나리오

### 5.1 기본 기능 테스트
1. 단일 툴 호출
2. 다중 툴 호출
3. 중첩된 툴 호출
4. 툴 없는 일반 응답

### 5.2 에러 상황 테스트
1. 잘못된 툴명 호출
2. 잘못된 인수 형식
3. 툴 실행 실패
4. 네트워크 연결 실패

### 5.3 성능 테스트
1. 대량 툴 호출 처리
2. 긴 대화 세션
3. 동시 다중 사용자

## 6. 배포 전 체크리스트

- [ ] 모든 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 기존 기능 호환성 확인
- [ ] 다양한 LLM 환경에서 테스트
- [ ] 성능 벤치마크 확인
- [ ] 문서화 완료
- [ ] 예제 코드 작성

## 7. 향후 개선 계획

### 7.1 Short-term (1-2주)
- 다양한 프롬프트 형식 지원
- 툴 호출 통계 및 모니터링
- 더 나은 에러 메시지

### 7.2 Long-term (1-2개월)
- AI 기반 툴 선택 최적화
- 동적 프롬프트 생성
- 툴 체이닝 자동화