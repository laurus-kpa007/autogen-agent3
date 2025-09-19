import asyncio
from orchestrator.llm_connector import get_llm_client
from autogen_agentchat.messages import TextMessage

async def test_direct_llm():
    """LLM 클라이언트 직접 테스트"""
    print("Testing direct LLM connection...")

    llm_client = get_llm_client()

    # 간단한 메시지 테스트
    messages = [
        TextMessage(content="CPU 사용률을 알려주세요", source="user")
    ]

    try:
        print("Calling LLM with TextMessage...")
        async for chunk in llm_client.create_stream(messages=messages):
            print(f"Chunk: {chunk}")
            if hasattr(chunk, 'content'):
                print(f"Content: {chunk.content}")
    except Exception as e:
        print(f"Error: {e}")

    # 딕셔너리 형태로도 테스트
    try:
        print("\nTrying with raw dict format...")
        import httpx
        import json

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:1234/v1/chat/completions",
                json={
                    "model": "gemma-3-4b-it",
                    "messages": [
                        {"role": "user", "content": "CPU 사용률을 알려주세요"}
                    ],
                    "stream": False
                }
            )
            result = response.json()
            print(f"Direct API response: {result['choices'][0]['message']['content']}")
    except Exception as e:
        print(f"Direct API error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_llm())