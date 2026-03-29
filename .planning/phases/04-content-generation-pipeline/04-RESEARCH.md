# Phase 4 Research: Content Generation Pipeline

**Phase:** 04-content-generation-pipeline
**Researched:** 2026-03-26
**Confidence:** HIGH

---

## Executive Summary

Phase 4 transforms DeckForge from a structured-IR renderer into an AI-powered presentation generator. A natural language prompt goes in; a complete, coherent Presentation IR comes out. The pipeline is four stages: intent parsing, outline generation, per-slide expansion, and cross-slide refinement. Each stage uses structured LLM output (JSON mode / function calling) to produce typed Pydantic models, not free-form text.

The LLM layer is model-agnostic via a custom adapter pattern (not LiteLLM -- see security section). Users can bring their own API key for Claude, OpenAI, Gemini, or Ollama. Progress streams to clients via SSE over Redis pub/sub (infrastructure already exists from Phase 1).

---

## 1. LLM Adapter Pattern

### Architecture: Abstract Base + Provider Implementations

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from pydantic import BaseModel

class CompletionResponse(BaseModel):
    content: str
    model: str
    usage: dict  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str

class StreamChunk(BaseModel):
    content: str
    finish_reason: str | None = None

class LLMAdapter(ABC):
    """Base adapter for all LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,  # JSON mode
    ) -> CompletionResponse: ...

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[dict],
        model: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> BaseModel: ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]: ...
```

### Provider Implementations (~150-200 lines each)

| Provider | SDK | Structured Output Method | Model Default |
|----------|-----|--------------------------|---------------|
| Claude | `anthropic>=0.52` | Tool use with single-tool pattern | claude-sonnet-4-20250514 |
| OpenAI | `openai>=1.70` | `response_format={"type": "json_schema", "json_schema": ...}` | gpt-4o |
| Gemini | `google-generativeai>=0.8` | `response_mime_type="application/json"` + `response_schema` | gemini-2.0-flash |
| Ollama | `httpx` (REST API) | JSON mode via `format: "json"` in API call | llama3.1:8b |

### Router with Fallback Chains

```python
class LLMRouter:
    """Routes requests to the appropriate adapter with fallback."""

    def __init__(self, adapters: dict[str, LLMAdapter], fallback_chain: list[str]):
        self.adapters = adapters
        self.fallback_chain = fallback_chain  # e.g., ["claude", "openai", "gemini"]

    async def complete(self, messages, model=None, **kwargs) -> CompletionResponse:
        provider = self._resolve_provider(model)
        for provider_name in [provider] + [f for f in self.fallback_chain if f != provider]:
            try:
                return await self.adapters[provider_name].complete(messages, model, **kwargs)
            except (RateLimitError, ServiceUnavailableError):
                continue
        raise AllProvidersFailedError()
```

### BYO Key Support (CONTENT-06)

User-provided API keys are passed per-request, never stored in the database. The router creates a temporary adapter instance with the user's key:

```python
class LLMConfig(BaseModel):
    provider: str  # "claude", "openai", "gemini", "ollama"
    model: str | None = None
    api_key: str | None = None  # User's own key
    base_url: str | None = None  # For Ollama or custom endpoints
```

### Why NOT LiteLLM

**Decision: Custom adapters over LiteLLM.**

LiteLLM 1.82.7-1.82.8 contained credential-stealing malware (March 2026 supply chain attack). While 1.82.6 is safe, the trust recovery timeline is uncertain. The LiteLLM team has paused all releases pending a supply chain review.

Custom adapters cost ~600 lines total (4 providers x ~150 lines) and provide:
- Zero supply chain risk (each official SDK is maintained by the provider)
- Full control over structured output parsing per provider
- No transitive dependency bloat (LiteLLM pulls 50+ deps)
- Simpler debugging (direct SDK calls, not abstraction layers)

The only thing lost is LiteLLM's cost tracking, which DeckForge handles via its own credit system anyway.

**SDK versions (verified March 2026):**
- `anthropic>=0.52.0` -- Anthropic official SDK
- `openai>=1.70.0` -- OpenAI official SDK
- `google-generativeai>=0.8.0` -- Google AI SDK
- `httpx>=0.28` -- Already in deps, used for Ollama REST calls

---

## 2. Structured Output from LLMs

### The Core Problem

Each pipeline stage produces typed output (intent, outline, slide content). Free-form text output requires brittle regex/string parsing. Structured output guarantees valid JSON matching a Pydantic schema.

### Per-Provider Strategy

**Claude (Anthropic):**
- Use tool_use with a single tool whose input_schema matches the Pydantic model's JSON Schema
- The model "calls the tool" and the structured data is in `tool_use.input`
- Temperature 0 for deterministic structure, higher for creative content
- Pydantic `model_validate(tool_call.input)` for parsing

**OpenAI:**
- Native structured outputs via `response_format={"type": "json_schema", "json_schema": schema}`
- Guarantees output conforms to schema (not just valid JSON -- schema-valid JSON)
- Available on gpt-4o and later models

**Gemini:**
- `generation_config.response_mime_type = "application/json"`
- `generation_config.response_schema = schema_dict`
- Works on gemini-2.0-flash and gemini-2.0-pro

**Ollama:**
- `format: "json"` in the API request body
- No schema enforcement -- model outputs JSON but structure is best-effort
- Validation via Pydantic with retry on parse failure (up to 3 attempts)

### Pydantic Parsing Pattern

```python
async def complete_structured(self, messages, model, response_model, **kwargs):
    # Get raw JSON from provider-specific structured output
    raw = await self._get_structured_json(messages, model, **kwargs)
    # Parse with Pydantic -- raises ValidationError on schema mismatch
    return response_model.model_validate(raw)
```

### Retry on Parse Failure

For providers without schema enforcement (Ollama), retry up to 3 times with the validation error included in the prompt:

```python
for attempt in range(3):
    try:
        return response_model.model_validate(raw_json)
    except ValidationError as e:
        messages.append({"role": "user", "content": f"JSON was invalid: {e}. Fix and retry."})
```

---

## 3. Content Pipeline Stages

### Stage 1: Intent Parsing (CONTENT-01)

**Input:** Natural language prompt + generation_options
**Output:** `ParsedIntent` Pydantic model

```python
class ParsedIntent(BaseModel):
    purpose: Purpose  # From IR enums
    audience: Audience
    topic: str
    key_messages: list[str]  # 3-7 core messages
    target_slide_count: int  # Resolved from generation_options or inferred
    tone: Tone
    suggested_slide_types: list[SlideType]  # Recommended types
    data_references: list[str]  # Any data/numbers mentioned in prompt
```

The intent parser extracts structure from the prompt. It maps natural language to DeckForge's enum types (Purpose, Audience, Tone). If generation_options specifies target_slide_count, it is honored. Otherwise, the LLM infers based on topic complexity.

### Stage 2: Outline Generation (CONTENT-02)

**Input:** `ParsedIntent`
**Output:** `PresentationOutline` Pydantic model

```python
class SlideOutline(BaseModel):
    position: int
    slide_type: SlideType
    headline: str  # <=8 words, "so what?" test
    key_points: list[str]  # 2-4 points per slide
    narrative_role: str  # "opening", "evidence", "transition", "conclusion"
    data_needs: list[str] | None = None  # What data this slide needs

class PresentationOutline(BaseModel):
    title: str
    narrative_arc: str  # "pyramid", "scr", "mece", "chronological"
    sections: list[str]  # High-level section names
    slides: list[SlideOutline]
```

**Narrative Arc Frameworks:**

| Framework | When to Use | Structure |
|-----------|-------------|-----------|
| Pyramid Principle | Board meetings, exec summaries | Lead with conclusion, then supporting evidence |
| SCR (Situation-Complication-Resolution) | Problem-solving, strategy | Set context, identify problem, propose solution |
| MECE (Mutually Exclusive, Collectively Exhaustive) | Analysis, market sizing | No overlap, no gaps in coverage |
| Chronological | Project updates, timelines | Past -> Present -> Future |

The LLM selects the appropriate framework based on the parsed intent's purpose and audience. The prompt includes framework descriptions and examples.

### Stage 3: Per-Slide Content Expansion (CONTENT-03)

**Input:** `PresentationOutline` + `ParsedIntent`
**Output:** List of slide IR dicts (ready for Presentation model)

Each slide in the outline is expanded into full IR with:
- **Headline:** <=8 words, passes the "so what?" test (not descriptive, but assertive)
- **Body content:** Bullets <=12 words each, concise and action-oriented
- **Speaker notes:** 2-3 sentences expanding on the slide's key message
- **Elements:** Appropriate elements for the slide type (bullet_list for bullets, table for data, chart for visualizations)
- **Layout hint:** Based on content volume and slide type

Expansion happens one slide at a time (not batch) to stay within context limits and allow per-slide progress updates.

### Stage 4: Cross-Slide Refinement (CONTENT-04)

**Input:** Full list of expanded slides + `ParsedIntent`
**Output:** Refined list of slides (same structure, improved consistency)

The refiner checks and fixes:
- **Terminology consistency:** Same concepts use same terms across all slides
- **Tense consistency:** All slides use same tense (present for recommendations, past for results)
- **Style consistency:** Capitalization, punctuation, bullet formatting
- **Redundancy elimination:** Merge or remove slides that repeat the same point
- **Flow verification:** Transitions between slides feel natural
- **Headline quality:** Every headline passes the "so what?" test

The refiner receives ALL slides at once (not individually) to detect cross-slide issues. This is the most token-expensive stage but critical for quality.

---

## 4. Prompt Engineering Strategy

### Template Structure

Each pipeline stage has a dedicated prompt template with:

```python
class PromptTemplate:
    system_prompt: str  # Role + constraints + output format
    user_template: str  # Jinja2 template with {{variables}}
    examples: list[dict]  # Few-shot examples (1-2 per stage)
    output_schema: type[BaseModel]  # Expected response model
```

### Key Prompt Engineering Principles

1. **Structured system prompts:** Define the role ("You are a presentation strategist"), constraints ("Headlines must be <=8 words"), and output format (JSON schema).

2. **Few-shot examples:** Include 1-2 examples of good output per stage. These dramatically improve output quality and schema adherence.

3. **Negative examples for common failures:** "Do NOT use descriptive headlines like 'Revenue Overview'. DO use assertive headlines like 'Revenue Grew 23% YoY'."

4. **Chain the context:** Each stage receives the output of the previous stage as context, not the raw prompt. The intent parser output feeds the outliner, not the original prompt.

5. **Token budget awareness:** Each stage prompt includes the target token limit. The outliner knows the target slide count. The expander knows the density setting.

### Content Quality Rules (embedded in prompts)

| Rule | Enforcement |
|------|-------------|
| Headline <=8 words | Pydantic validator + prompt instruction |
| Bullet <=12 words | Pydantic validator + prompt instruction |
| "So what?" test | Prompt: "Every headline must make an assertion, not a description" |
| No jargon without definition | Prompt: "If using technical terms, include a plain-English parenthetical" |
| Data-backed claims | Prompt: "Every claim slide must reference a data point or source" |

---

## 5. SSE Streaming from FastAPI (API-13)

### Existing Infrastructure

Phase 1 already built:
- `publish_progress()` in `workers/tasks.py` -- publishes to Redis `job:{job_id}:progress` channel
- `Job` model with status/progress tracking
- Redis pub/sub infrastructure

### SSE Endpoint Design

```python
from sse_starlette.sse import EventSourceResponse

@router.get("/generate/{job_id}/stream")
async def stream_generation_progress(
    job_id: uuid.UUID,
    redis: RedisClient,
    api_key: CurrentApiKey,
) -> EventSourceResponse:
    """Stream generation progress events via SSE."""

    async def event_generator():
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"job:{job_id}:progress")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield {
                        "event": data["stage"],
                        "data": json.dumps(data),
                    }
                    if data["stage"] in ("complete", "failed"):
                        break
        finally:
            await pubsub.unsubscribe(f"job:{job_id}:progress")

    return EventSourceResponse(event_generator())
```

### SSE Event Types

| Event | Stage | Progress | Data |
|-------|-------|----------|------|
| `intent_parsed` | parsing | 0.15 | ParsedIntent summary |
| `outline_generated` | outlining | 0.35 | Slide count, section names |
| `slide_expanded` | writing | 0.35-0.80 | Slide index, headline |
| `refinement_complete` | refining | 0.90 | Changes made count |
| `rendering` | rendering | 0.95 | Rendering started |
| `complete` | complete | 1.0 | Job result with deck ID |
| `failed` | failed | - | Error message |

### SSE Considerations

- **sse-starlette** (already in STACK.md) handles W3C spec compliance, automatic disconnect detection, and graceful shutdown
- **Timeout:** 120 seconds server-side (generation should complete well within this)
- **Reconnection:** SSE has built-in reconnection via `Last-Event-ID` header; include event IDs
- **Corporate proxy fallback:** Some proxies buffer SSE. The polling endpoint (GET /v1/jobs/{job_id}) already exists as fallback

---

## 6. LiteLLM Security Assessment

### Current Status (March 2026)

- **Compromised versions:** 1.82.7 and 1.82.8 contained credential-stealing malware
- **Attack vector:** Maintainer account compromised via trojanized security scanner
- **Safe version:** 1.82.6 (verified, pre-compromise)
- **Release status:** All releases PAUSED pending supply chain review

### Decision: Do NOT use LiteLLM

Given:
1. Supply chain trust is unrecovered
2. Release pipeline is frozen (no security patches)
3. Custom adapters are ~600 lines total
4. Each provider's official SDK is maintained by a well-resourced company
5. DeckForge needs only `complete()`, `complete_structured()`, and `stream()` -- not LiteLLM's 100+ model routing

**Action:** Build custom `LLMAdapter` implementations wrapping official SDKs. Add `anthropic`, `openai`, and `google-generativeai` to pyproject.toml. Use `httpx` (already a dependency) for Ollama.

### Dependency Additions

```toml
# LLM Provider SDKs (official, no LiteLLM)
"anthropic>=0.52.0",
"openai>=1.70.0",
"google-generativeai>=0.8.0",
# sse-starlette for SSE streaming
"sse-starlette>=3.3.3",
```

---

## 7. Content Quality Framework

### Headline Rules

| Quality Level | Example | Assessment |
|---------------|---------|------------|
| Bad | "Revenue" | No assertion, no insight |
| Mediocre | "Revenue Overview" | Descriptive, not assertive |
| Good | "Revenue Grew 23% YoY" | Assertive, data-backed |
| Excellent | "Revenue Growth Accelerating Despite Market Headwinds" | Assertive, contextual, compelling |

**Enforcement:** Pydantic validators on headline length (<=8 words). Prompt instructions for assertive tone. Refinement stage checks all headlines.

### Bullet Conciseness Rules

- Maximum 12 words per bullet point
- Start with action verb or key noun
- No sub-bullets in the IR (flatten to top-level bullets)
- Maximum 5-6 bullets per slide (density setting controls this)

### "So What?" Test

Every content-bearing slide must answer: "Why should the audience care about this?" If a slide is purely descriptive ("Q3 Revenue was $4.2M"), the refiner transforms it into an assertion ("Q3 Revenue Beat Forecast by 12%").

### Density Control

The `generation_options.density` enum controls content volume:

| Density | Bullets/Slide | Words/Bullet | Speaker Notes |
|---------|---------------|--------------|---------------|
| sparse | 2-3 | <=8 | Full paragraphs |
| balanced | 3-5 | <=12 | 2-3 sentences |
| dense | 5-7 | <=12 | Brief notes |

---

## 8. POST /v1/generate Endpoint Design (API-02)

### Request Schema

```python
class GenerateRequest(BaseModel):
    prompt: str  # Natural language description
    generation_options: GenerationOptions | None = None  # From IR
    theme: str = "executive-dark"
    brand_kit: BrandKit | None = None
    llm_config: LLMConfig | None = None  # BYO key support
    webhook_url: str | None = None
```

### Response Flow

1. **POST /v1/generate** -- Returns `GenerateResponse(job_id=..., status="queued")`
2. **GET /v1/generate/{job_id}/stream** -- SSE stream of progress events
3. **GET /v1/jobs/{job_id}** -- Polling fallback for status + result
4. On completion, result contains `deck_id` and `download_url`

### Worker Task Flow

```
generate_content(prompt, llm_config, generation_options)
  -> intent_parser.parse(prompt)        [SSE: intent_parsed]
  -> outliner.generate(intent)          [SSE: outline_generated]
  -> for slide in outline:
       writer.expand(slide, intent)     [SSE: slide_expanded]
  -> refiner.refine(all_slides, intent) [SSE: refinement_complete]
  -> build Presentation IR
  -> render_pipeline(presentation)      [SSE: rendering]
  -> upload to S3                       [SSE: complete]
```

---

## Architecture Diagram

```
POST /v1/generate
        |
        v
   [ARQ Worker - Content Pool]
        |
   (1) IntentParser -----> ParsedIntent
        |
   (2) Outliner ---------> PresentationOutline
        |
   (3) SlideWriter ------> List[SlideIR]  (one LLM call per slide)
        |
   (4) CrossSlideRefiner -> List[SlideIR]  (one LLM call, all slides)
        |
   (5) Build Presentation IR
        |
   (6) render_pipeline() ---------> PPTX bytes
        |
   (7) Upload to S3
        |
   SSE: complete
```

Each numbered step publishes progress via `publish_progress()` to Redis pub/sub.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM output doesn't match Pydantic schema | MEDIUM | HIGH | Structured output + retry with error feedback |
| Token costs exceed expectations | LOW | MEDIUM | Track usage per stage, expose in API response |
| Ollama structured output unreliable | HIGH | LOW | 3x retry with validation feedback, graceful degradation |
| SSE connections accumulate | LOW | MEDIUM | 120s timeout, sse-starlette auto-disconnect |
| Cross-slide refinement too token-expensive | MEDIUM | MEDIUM | Batch all slides into one call, set max_tokens |

---

## Sources

### Verified (HIGH confidence)
- [Anthropic tool use docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) -- Structured output via tool_use
- [OpenAI structured outputs](https://platform.openai.com/docs/guides/structured-outputs) -- JSON schema enforcement
- [Google Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output) -- response_schema parameter
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) -- v3.3.3, production SSE for FastAPI
- [FastAPI SSE docs](https://fastapi.tiangolo.com/advanced/custom-response/#eventstream) -- SSE response patterns
- [LiteLLM Security Advisory](https://docs.litellm.ai/blog/security-update-march-2026) -- Supply chain attack details

### Verified with caveats (MEDIUM confidence)
- [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md) -- JSON mode format parameter
- [Pyramid Principle (Minto)](https://www.amazon.com/Pyramid-Principle-Logic-Writing-Thinking/dp/0273710516) -- Narrative framework
- [McKinsey "So What?" test](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights) -- Content quality heuristic
