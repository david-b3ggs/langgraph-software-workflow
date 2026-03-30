from functools import lru_cache
from langchain_anthropic import ChatAnthropic
from src.config import settings


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.2) -> ChatAnthropic:
    """Return a cached ChatAnthropic instance. LangSmith tracing
    activates automatically when LANGSMITH_API_KEY is set in env."""
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=8096,
    )
