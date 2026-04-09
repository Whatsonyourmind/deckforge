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
    build_cached_system,
)
from deckforge.llm.batch import (
    BatchLLMJob,
    BatchResult,
    BatchState,
    BatchStatus,
)
from deckforge.llm.router import (
    TIER_MODEL_MAP,
    LLMRouter,
    LLMTier,
    create_router,
)

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
    "build_cached_system",
    # Batch API
    "BatchLLMJob",
    "BatchResult",
    "BatchState",
    "BatchStatus",
    # Router
    "LLMRouter",
    "LLMTier",
    "TIER_MODEL_MAP",
    "create_router",
]
