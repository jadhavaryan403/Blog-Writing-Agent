"""
app/langgraph/llm.py
─────────────────────
Centralised LLM factory.
Returns a LangChain ChatOpenAI instance configured from settings.
LangSmith tracing is enabled globally via env vars.
"""

import os
from langchain_groq import ChatGroq
from app.core.config import settings

# Set LangSmith env vars so every LangChain call is traced automatically
os.environ.setdefault("LANGCHAIN_TRACING_V2", str(settings.LANGCHAIN_TRACING_V2).lower())
os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGCHAIN_API_KEY)
os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT)
os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.LANGCHAIN_ENDPOINT)


def get_llm(temperature: float | None = None) -> ChatGroq:
    """Return a ChatGroq instance.

    Every call creates a new instance so callers can tune temperature
    independently (e.g. Writer uses higher temp, Reviewer uses 0).
    """
    return ChatGroq(
        model=settings.GROQ_MODEL,
        temperature=temperature if temperature is not None else settings.GROQ_TEMPERATURE,
        api_key=settings.GROQ_API_KEY,
    )


def get_guard_llm(temperature: float | None = 0.1) -> ChatGroq:
    """Return a small llm model instance for guardrail"""
    return ChatGroq(
        model='openai/gpt-oss-20b',
        temperature=temperature,
        api_key=settings.GROQ_API_KEY,
        model_kwargs={
        "response_format": {"type": "json_object"}
                    }
    )