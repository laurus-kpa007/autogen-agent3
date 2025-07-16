from autogen_ext.models.openai import OpenAIChatCompletionClient
from orchestrator.config import LLM_CONFIG

def get_llm_client():
    return OpenAIChatCompletionClient(
        model=LLM_CONFIG["model"],
        base_url=LLM_CONFIG["base_url"],
        api_key=LLM_CONFIG["api_key"],
#        model_info={"family": "unknown", "function_calling": True, "vision": False}
    )
