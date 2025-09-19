# 데이터 흐름 다이어그램: Tool Calling 방식 비교

## 1. Function Calling 방식 상세 데이터 흐름

### 1.1 전체 시스템 흐름

```mermaid
sequenceDiagram
    participant U as User
    participant AB as agent_builder
    participant AF as AgentFactory
    participant AA as AssistantAgent
    participant LC as LLM_Client
    participant API as OpenAI_API
    participant MCP as MCP_Server

    U->>AB: create_orchestrator_agent()
    AB->>AF: create_agent()
    AF->>AF: detect_function_calling_support()
    Note over AF: function_calling: true 감지
    AF->>AA: AssistantAgent(tools=mcp_tools)
    AA-->>AB: agent instance
    AB-->>U: agent

    U->>AA: run("시스템 정보 알려줘")
    AA->>LC: create_stream(messages, tools)
    LC->>API: POST /chat/completions
    Note over API: tools 배열과 함께 요청
    API-->>LC: function_call 포함 응답
    LC->>AA: tool_call_request_event
    AA->>MCP: execute_tool(tool_call)
    MCP-->>AA: tool_result
    AA->>LC: create_stream(updated_messages)
    LC->>API: POST /chat/completions
    API-->>LC: final_response
    LC-->>AA: text_message
    AA-->>U: 최종 응답
```

### 1.2 메시지 구조 변화

```mermaid
graph TD
    A[Initial Messages] --> B[Add Tools Schema]
    B --> C[LLM Request with Tools]
    C --> D[Function Call Response]
    D --> E[Execute Tool]
    E --> F[Add Tool Result to Messages]
    F --> G[Second LLM Request]
    G --> H[Final Text Response]

    subgraph "메시지 구조"
        I["[
          {role: 'system', content: 'system_prompt'},
          {role: 'user', content: '시스템 정보 알려줘'}
        ]"]

        J["[
          ...이전 메시지,
          {role: 'assistant', tool_calls: [{id: 'call_1', function: {name: 'get_system_info', arguments: '{}'}}]},
          {role: 'tool', tool_call_id: 'call_1', content: 'CPU: 80%, RAM: 60%'}
        ]"]

        K["[
          ...이전 메시지,
          {role: 'assistant', content: '현재 시스템 상태는...'}
        ]"]
    end

    C --> I
    F --> J
    H --> K
```

## 2. Prompt-Based 방식 상세 데이터 흐름

### 2.1 전체 시스템 흐름

```mermaid
sequenceDiagram
    participant U as User
    participant AB as agent_builder
    participant AF as AgentFactory
    participant PA as PromptBasedAgent
    participant TCP as ToolCallParser
    participant LC as LLM_Client
    participant API as OpenAI_API
    participant MCP as MCP_Server

    U->>AB: create_orchestrator_agent()
    AB->>AF: create_agent()
    AF->>AF: detect_function_calling_support()
    Note over AF: function_calling: false 감지
    AF->>TCP: create_system_prompt(tools)
    TCP-->>AF: enhanced_system_prompt
    AF->>PA: PromptBasedAgent(enhanced_prompt)
    PA-->>AB: agent instance
    AB-->>U: agent

    U->>PA: run("시스템 정보 알려줘")

    loop Tool Iteration (max 5회)
        PA->>LC: create_stream(messages)
        LC->>API: POST /chat/completions
        Note over API: enhanced prompt로 요청
        API-->>LC: xml_style_response
        LC-->>PA: response_text
        PA->>TCP: parse_tool_calls(response)

        alt Tool Call 발견
            TCP-->>PA: [ToolCall(name, args)]
            PA->>MCP: execute_tool(tool_call)
            MCP-->>PA: tool_result
            PA->>TCP: format_tool_result(result)
            TCP-->>PA: formatted_result
            PA->>PA: add_to_conversation(result)
        else Tool Call 없음
            PA-->>U: 최종 응답
        end
    end
```

### 2.2 프롬프트 진화 과정

```mermaid
graph TD
    A[기본 System Prompt] --> B[Tool Descriptions 추가]
    B --> C[Tool Call Format 정의]
    C --> D[Enhanced System Prompt]

    D --> E[First LLM Call]
    E --> F[XML Response with Tool Call]
    F --> G[Parse Tool Call]
    G --> H[Execute Tool]
    H --> I[Format Tool Result]
    I --> J[Add to Conversation]
    J --> K[Second LLM Call]
    K --> L[Final Response]

    subgraph "프롬프트 구조"
        M["당신은 오케스트레이터 AI입니다.

        사용 가능한 도구:
        - get_system_info: 시스템 정보 조회

        도구 호출 형식:
        <tool_call>
        <name>도구명</name>
        <arguments>{}</arguments>
        </tool_call>"]

        N["User: 시스템 정보 알려줘

        Assistant: <tool_call>
        <name>get_system_info</name>
        <arguments>{}</arguments>
        </tool_call>

        <tool_result name='get_system_info'>
        CPU: 80%, RAM: 60%
        </tool_result>"]

        O["Assistant: 현재 시스템 상태는 다음과 같습니다:
        - CPU 사용률: 80%
        - 메모리 사용률: 60%"]
    end

    D --> M
    J --> N
    L --> O
```

## 3. 에이전트 선택 플로우

### 3.1 AgentFactory 결정 로직

```mermaid
flowchart TD
    A[AgentFactory.create_agent 호출] --> B[get_llm_client]
    B --> C[load_mcp_tools]
    C --> D[detect_function_calling_support]

    D --> E{model_client.model_info 존재?}
    E -->|Yes| F{model_info.function_calling?}
    E -->|No| G{parallel_tool_calls 설정?}

    F -->|True| H[Function Calling 지원]
    F -->|False| I[Function Calling 미지원]

    G -->|True| H
    G -->|False| I

    H --> J{tools 존재?}
    J -->|Yes| K[AssistantAgent 생성]
    J -->|No| L[PromptBasedAgent 생성]

    I --> M[PromptBasedAgent 생성]

    K --> N[기존 AutoGen 워크플로우]
    L --> O[프롬프트 기반 워크플로우]
    M --> O

    subgraph "AssistantAgent 구성"
        P[model_client + tools + system_message]
        Q[reflect_on_tool_use: True]
        R[model_client_stream: True]
        S[max_tool_iterations: 5]
    end

    subgraph "PromptBasedAgent 구성"
        T[model_client + enhanced_system_prompt]
        U[tools_dict + conversation_history]
        V[max_tool_iterations: 5]
    end

    K --> P
    M --> T
```

## 4. 메시지 처리 비교

### 4.1 Function Calling 메시지 플로우

```mermaid
graph LR
    subgraph "메시지 변환"
        A[User Message] --> B[System + User Messages]
        B --> C[Add Tools Schema]
        C --> D[LLM Request]
        D --> E[Function Call Response]
        E --> F[Tool Execution]
        F --> G[Tool Message Added]
        G --> H[Final LLM Request]
        H --> I[Text Response]
    end

    subgraph "메시지 형식"
        J["ChatMessage Object
        - source: 'user'
        - content: '질문'"]

        K["API Request
        - messages: [...]
        - tools: [...]
        - tool_choice: 'auto'"]

        L["Tool Call
        {
          'id': 'call_123',
          'function': {
            'name': 'tool_name',
            'arguments': '{}'
          }
        }"]

        M["Tool Result
        {
          'role': 'tool',
          'tool_call_id': 'call_123',
          'content': 'result'
        }"]
    end

    A --> J
    D --> K
    E --> L
    F --> M
```

### 4.2 Prompt-Based 메시지 플로우

```mermaid
graph LR
    subgraph "메시지 변환"
        A[User Message] --> B[Enhanced System Prompt]
        B --> C[Conversation History]
        C --> D[LLM Request]
        D --> E[XML Response]
        E --> F[Parse Tool Calls]
        F --> G[Execute Tools]
        G --> H[Format Results]
        H --> I[Update Conversation]
        I --> J[Next LLM Request]
        J --> K[Final Response]
    end

    subgraph "데이터 구조"
        L["conversation_history = [
          {'role': 'system', 'content': 'enhanced_prompt'},
          {'role': 'user', 'content': '질문'}
        ]"]

        M["XML Response:
        '시스템 정보를 확인하겠습니다.

        <tool_call>
        <name>get_system_info</name>
        <arguments>{}</arguments>
        </tool_call>'"]

        N["Parsed ToolCall:
        ToolCall(
          name='get_system_info',
          arguments={}
        )"]

        O["Formatted Result:
        '<tool_result name=\"get_system_info\">
        CPU: 80%, RAM: 60%
        </tool_result>'"]
    end

    C --> L
    E --> M
    F --> N
    H --> O
```

## 5. 성능 및 리소스 사용 비교

### 5.1 토큰 사용량 분석

```mermaid
graph TD
    subgraph "Function Calling 토큰 사용"
        A[System Prompt: ~100 tokens]
        B[User Message: ~20 tokens]
        C[Tools Schema: ~200 tokens]
        D[Function Call Response: ~50 tokens]
        E[Tool Result: ~100 tokens]
        F[Final Response: ~150 tokens]

        G[총 토큰: ~620 tokens]
    end

    subgraph "Prompt-Based 토큰 사용"
        H[Enhanced System Prompt: ~300 tokens]
        I[User Message: ~20 tokens]
        J[First Response with Tool Call: ~100 tokens]
        K[Tool Result in Context: ~150 tokens]
        L[Second Request Context: ~470 tokens]
        M[Final Response: ~150 tokens]

        N[총 토큰: ~1190 tokens]
    end

    A --> G
    H --> N

    O[토큰 효율성: Function Calling > Prompt-Based]
```

### 5.2 응답 시간 비교

```mermaid
gantt
    title 응답 시간 비교
    dateFormat X
    axisFormat %s

    section Function Calling
    LLM Request 1    :0, 2
    Tool Execution   :2, 3
    LLM Request 2    :3, 5
    Total Time       :0, 5

    section Prompt-Based
    LLM Request 1    :0, 2
    Parsing          :2, 2.2
    Tool Execution   :2.2, 3.2
    Context Building :3.2, 3.5
    LLM Request 2    :3.5, 5.5
    Total Time       :0, 5.5
```

## 6. 에러 처리 플로우

### 6.1 Function Calling 에러 처리

```mermaid
graph TD
    A[Function Call 시도] --> B{호출 성공?}
    B -->|Yes| C[Tool 실행]
    B -->|No| D[에러 메시지 생성]

    C --> E{실행 성공?}
    E -->|Yes| F[결과 반환]
    E -->|No| G[Tool 에러 메시지]

    D --> H[사용자에게 에러 알림]
    G --> I[에러 컨텍스트로 재시도]

    I --> J[LLM이 에러 해석]
    J --> K[대안 제시 또는 종료]
```

### 6.2 Prompt-Based 에러 처리

```mermaid
graph TD
    A[XML 파싱 시도] --> B{파싱 성공?}
    B -->|Yes| C[Tool Call 추출]
    B -->|No| D[파싱 에러]

    C --> E{Tool 존재?}
    E -->|Yes| F[Tool 실행]
    E -->|No| G[Unknown Tool 에러]

    F --> H{실행 성공?}
    H -->|Yes| I[결과 포맷팅]
    H -->|No| J[Tool 실행 에러]

    D --> K[재시도 또는 일반 응답]
    G --> L[사용 가능한 Tool 목록 제시]
    J --> M[에러 메시지 포맷팅]

    K --> N[일반 텍스트 응답 생성]
    L --> O[올바른 형식 예시 제공]
    M --> P[에러 컨텍스트로 계속]
```

## 7. 확장성 및 유지보수성

### 7.1 새로운 Tool 추가 플로우

```mermaid
graph LR
    subgraph "Function Calling"
        A[MCP Server에 Tool 추가] --> B[AutoGen이 자동 스키마 생성]
        B --> C[LLM이 스키마 기반 호출]
        C --> D[즉시 사용 가능]
    end

    subgraph "Prompt-Based"
        E[MCP Server에 Tool 추가] --> F[ToolCallParser가 설명 생성]
        F --> G[Enhanced Prompt 업데이트]
        G --> H[LLM 학습 필요할 수 있음]
        H --> I[사용 가능]
    end

    J[새 Tool 추가 난이도: Function Calling < Prompt-Based]
```

### 7.2 디버깅 복잡도

```mermaid
graph TD
    subgraph "Function Calling 디버깅"
        A[Tool Schema 확인] --> B[LLM Response 분석]
        B --> C[Tool Execution 로그]
        C --> D[간단한 디버깅]
    end

    subgraph "Prompt-Based 디버깅"
        E[Prompt 효과성 확인] --> F[XML 파싱 결과 분석]
        F --> G[Tool Call 추출 검증]
        G --> H[Context Building 확인]
        H --> I[복잡한 디버깅]
    end

    J[디버깅 복잡도: Function Calling < Prompt-Based]
```

이 문서는 두 가지 Tool Calling 방식의 상세한 데이터 흐름과 아키텍처 차이를 시각적으로 비교 분석하여, 개발자가 적절한 방식을 선택할 수 있도록 도움을 제공합니다.