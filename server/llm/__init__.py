# ==============================================================================
# server/llm/__init__.py — LLM 适配器工厂
# 根据配置创建对应的 LLM 适配器实例
# ==============================================================================

from server.config import DEEPSEEK_API_KEY, OPENAI_API_KEY
from server.config import LLM_PROVIDER as _default_provider
from server.llm.deepseek import DeepSeekAdapter
from server.llm.openai import OpenAIAdapter


def create_llm_adapter(provider: str = None):
    """
    创建 LLM 适配器实例。
    
    Args:
        provider: "deepseek" / "openai". 默认为 LLM_PROVIDER 环境变量.
    
    Returns:
        LLMAdapter 实例
    """
    provider = provider or _default_provider
    
    if provider == "openai":
        return OpenAIAdapter(api_key=OPENAI_API_KEY or "", model="gpt-4o")
    
    return DeepSeekAdapter(api_key=DEEPSEEK_API_KEY or "", model="deepseek-chat")
