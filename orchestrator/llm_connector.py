from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo
from orchestrator.config import LLM_CONFIG

def get_llm_client():
    return OpenAIChatCompletionClient(
        model=LLM_CONFIG["model"],
        base_url=LLM_CONFIG["base_url"],
        api_key=LLM_CONFIG["api_key"],
        model_info=ModelInfo(
            vision=False,
            function_calling=False,
            json_output=False,
            family="openai",
            structured_output=False
        ),
        parallel_tool_calls=False  # ✅ 여기서 설정
    )
