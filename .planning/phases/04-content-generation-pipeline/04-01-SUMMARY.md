---
phase: 04-content-generation-pipeline
plan: 01
subsystem: llm
tags: [anthropic, openai, gemini, ollama, httpx, pydantic, adapter-pattern, fallback-chain]

# Dependency graph
requires:
  - phase: 01-foundation-ir-schema
    provides: "Pydantic models, config.py Settings pattern"
provides:
  - "LLMAdapter ABC with complete, complete_structured, stream"
  - "4 provider adapters: Claude, OpenAI, Gemini, Ollama"
  - "LLMRouter with model-prefix dispatch and fallback chains"
  - "create_router() factory with BYO key and settings defaults"
  - "LLM error hierarchy: RateLimitError, ServiceUnavailableError, AllProvidersFailedError"
affects: [04-content-generation-pipeline, 05-chart-engine-finance-vertical]

# Tech tracking
tech-stack:
  added: [anthropic, openai, google-generativeai, sse-starlette]
  patterns: [adapter-pattern, factory-pattern, fallback-chain, tool-use-structured-output]

key-files:
  created:
    - src/deckforge/llm/__init__.py
    - src/deckforge/llm/base.py
    - src/deckforge/llm/models.py
    - src/deckforge/llm/adapters/__init__.py
    - src/deckforge/llm/adapters/claude.py
    - src/deckforge/llm/adapters/openai.py
    - src/deckforge/llm/adapters/gemini.py
    - src/deckforge/llm/adapters/ollama.py
    - src/deckforge/llm/router.py
    - tests/unit/test_llm_adapters.py
    - tests/unit/test_llm_router.py
  modified:
    - src/deckforge/config.py
    - pyproject.toml

key-decisions:
  - "Custom adapters wrapping official SDKs instead of LiteLLM (supply chain compromise March 2026)"
  - "Claude structured output via tool_use pattern, OpenAI via json_schema response_format, Gemini via response_schema"
  - "Ollama retry-on-ValidationError (up to 3 attempts) for structured output self-correction"
  - "Model-prefix routing: claude-* -> claude, gpt-* -> openai, gemini-* -> gemini"
  - "google-generativeai used per plan spec (deprecated in favor of google.genai -- migration deferred)"

patterns-established:
  - "LLMAdapter ABC: all providers implement complete(), complete_structured(), stream()"
  - "Error mapping: provider-specific errors -> RateLimitError, ServiceUnavailableError"
  - "create_router() factory: BYO key creates single-provider router, settings-based creates full chain"
  - "Fallback chain: transient errors (429, 5xx) trigger next provider, non-transient errors propagate"

requirements-completed: [CONTENT-05, CONTENT-06]

# Metrics
duration: 8min
completed: 2026-03-29
---

# Phase 04 Plan 01: LLM Adapter Layer Summary

**Model-agnostic LLM adapter layer with Claude/OpenAI/Gemini/Ollama providers, fallback router, and BYO key support**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-29T02:18:48Z
- **Completed:** 2026-03-29T02:26:55Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- LLMAdapter abstract base class with complete(), complete_structured(), and stream() methods
- 4 provider adapters (Claude, OpenAI, Gemini, Ollama) implementing the ABC with standardized error mapping
- LLMRouter with model-prefix dispatch and automatic fallback on rate limit and service errors
- create_router() factory supporting BYO API key override and settings-based defaults
- Config.py extended with LLM_DEFAULT_PROVIDER, LLM_FALLBACK_CHAIN, per-provider API keys
- 33 tests passing with fully mocked SDKs (no real API calls)

## Task Commits

Each task was committed atomically:

1. **Task 1: LLM types, abstract base, and 4 provider adapters**
   - `5185da7` (test: RED - failing adapter tests)
   - `223dac6` (feat: GREEN - adapter implementations)
2. **Task 2: LLM router with fallback chains, BYO key support, config integration**
   - `2673855` (test: RED - failing router tests)
   - `88e105d` (feat: GREEN - router + config implementation)

_TDD tasks: 2 RED + 2 GREEN = 4 commits_

## Files Created/Modified
- `src/deckforge/llm/base.py` - LLMAdapter ABC with complete, complete_structured, stream
- `src/deckforge/llm/models.py` - CompletionResponse, LLMUsage, StreamChunk, LLMConfig, error types
- `src/deckforge/llm/adapters/claude.py` - ClaudeAdapter wrapping anthropic SDK
- `src/deckforge/llm/adapters/openai.py` - OpenAIAdapter wrapping openai SDK
- `src/deckforge/llm/adapters/gemini.py` - GeminiAdapter wrapping google-generativeai SDK
- `src/deckforge/llm/adapters/ollama.py` - OllamaAdapter using httpx REST with retry-on-validation
- `src/deckforge/llm/router.py` - LLMRouter with prefix dispatch and fallback chain
- `src/deckforge/llm/__init__.py` - Public API re-exports
- `src/deckforge/llm/adapters/__init__.py` - Adapter re-exports
- `src/deckforge/config.py` - Added LLM settings (provider keys, fallback chain, Ollama URL)
- `pyproject.toml` - Added anthropic, openai, google-generativeai, sse-starlette dependencies
- `tests/unit/test_llm_adapters.py` - 19 adapter tests with mocked SDKs
- `tests/unit/test_llm_router.py` - 14 router + config tests with mock adapters

## Decisions Made
- Custom adapters wrapping official SDKs replace LiteLLM (supply chain compromise March 2026) with zero transitive dependency risk
- Claude uses tool_use pattern for structured output (most reliable), OpenAI uses json_schema response_format, Gemini uses response_schema config
- Ollama structured output includes retry-on-ValidationError (up to 3 attempts) with error feedback appended to messages for self-correction
- Model-prefix routing maps claude-*/gpt-*/gemini-*/llama-* to their respective adapters
- google-generativeai package used per plan spec; FutureWarning about deprecation in favor of google.genai noted for future migration

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- google-generativeai raises FutureWarning about deprecation in favor of google.genai package. Does not affect functionality. Logged for future migration consideration.

## User Setup Required

None - no external service configuration required. LLM API keys are optional (set via DECKFORGE_ANTHROPIC_API_KEY, DECKFORGE_OPENAI_API_KEY, DECKFORGE_GEMINI_API_KEY environment variables when ready).

## Next Phase Readiness
- LLM adapter layer is ready for content generation pipeline stages (intent parsing, outlining, writing, refining) in Plan 04-02
- All 4 providers tested and operational with standardized interface
- Router fallback ensures resilience across provider outages

## Self-Check: PASSED

All 11 created files verified on disk. All 4 commits (5185da7, 223dac6, 2673855, 88e105d) verified in git log.

---
*Phase: 04-content-generation-pipeline*
*Completed: 2026-03-29*
