"""LLM adapter layer for DeckForge.

Provides a model-agnostic interface across Claude, OpenAI, Gemini, and Ollama
with standardized error handling and structured output support.
"""

from deckforge.llm.base import LLMAdapter
from deckforge.llm.models import (
    AllProvidersFailedError,
    CompletionResponse,
    LLMConfig,
    LLMError,
    LLMUsage,
    RateLimitError,
    ServiceUnavailableError,
    StreamChunk,
)
from deckforge.llm.adapters import (
    ClaudeAdapter,
    GeminiAdapter,
    OllamaAdapter,
    OpenAIAdapter,
)
from deckforge.llm.router import LLMRouter, create_router

__all__ = [
    # Base
    "LLMAdapter",
    # Models
    "CompletionResponse",
    "LLMConfig",
    "LLMError",
    "LLMUsage",
    "RateLimitError",
    "ServiceUnavailableError",
    "AllProvidersFailedError",
    "StreamChunk",
    # Adapters
    "ClaudeAdapter",
    "GeminiAdapter",
    "OllamaAdapter",
    "OpenAIAdapter",
    # Router
    "LLMRouter",
    "create_router",
]
