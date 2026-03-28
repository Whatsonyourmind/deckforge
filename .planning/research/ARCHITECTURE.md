# Architecture Patterns

**Domain:** API-first AI slide generation platform
**Project:** DeckForge
**Researched:** 2026-03-26

## Recommended Architecture

Modular monolith with async workers. The IR (Intermediate Representation) is the backbone -- all inputs produce IR, all renderers consume IR. Clean module boundaries enable future extraction to microservices if needed.

### High-Level Data Flow

```
                    Structured Input (JSON IR)
                            |
                            v
Client --> FastAPI --> [Validate IR] --> Rendering Worker
               |                              |
               |                        [Theme Resolve]
               |                              |
               |                        [Layout Solve]
               |                              |
               |                     [Render to PPTX/Slides]
               |                              |
               |                         [QA Pipeline]
               |                              |
               |                      [Upload to R2]
               |                              |
               v                              v
         NL Input --> Content Worker    Download URL
                        |                   + QA Score
                   [Intent Parse]           + Credits Used
                        |
                   [Outline Gen]
                        |
                   [Content Expand]
                        |
                   [Content Refine]
                        |
                        v
                   Validated IR --> (same rendering path)
```

### Component Boundaries

| Component | Responsibility | Communicates With | Technology |
|-----------|---------------|-------------------|------------|
| api/ | HTTP routes, auth, rate limiting, billing gates | All modules via function calls | FastAPI, Pydantic |
| ir/ | Pydantic IR schema, validation, serialization | Consumed by layout/, rendering/, qa/ | Pydantic v2 |
| content/ | NL-to-IR pipeline (intent, outline, expand, refine) | LLM adapters, produces IR | LiteLLM, Pydantic |
| layout/ | Constraint-based layout solver, grid system | Consumes IR + Theme, produces positioned IR | kiwisolver, Pillow |
| rendering/pptx/ | python-pptx renderer | Consumes positioned IR, produces .pptx bytes | python-pptx, lxml |
| rendering/gslides/ | Google Slides API renderer | Consumes positioned IR, produces Slides URL | google-api-python-client |
| themes/ | Theme registry, brand kit overlay, style resolution | Consumed by layout/ and rendering/ | PyYAML |
| charts/ | Chart builder: native (python-pptx) + static (Plotly) | Consumed by rendering modules | python-pptx, Plotly, Kaleido |
| finance/ | Finance-specific layouts, calculations, formatting | Produces finance IR elements, consumed by charts/ | Custom |
| qa/ | 5-pass QA pipeline, autofix, scoring | Reads rendered output + IR, produces QA report | Pillow, custom rules |
| workers/ | Async task definitions, webhooks, storage upload | ARQ tasks wrapping content/ and rendering/ | ARQ, Redis, boto3 |
| db/ | SQLAlchemy models, repositories | Used by api/ for persistence | SQLAlchemy, psycopg3 |

### Module Communication Contracts (Critical Rules)

1. **content/ ONLY produces IR** -- never touches rendering, never calls python-pptx
2. **rendering/ consumes IR** -- never calls LLMs, never modifies content
3. **layout/ adds geometry** -- adds x, y, width, height to elements; never modifies content text
4. **themes/ resolves variables** -- converts theme references to concrete color/font values
5. **qa/ is read-only by default** -- autofix returns patches (IR diffs), does not mutate directly
6. **llm/ adapters normalize ALL models** -- every provider returns the same Pydantic response schema

### Data Flow Details

**Structured API flow (synchronous for <=10 slides):**
1. Client POSTs JSON IR to /v1/render
2. FastAPI validates IR against Pydantic schema
3. Theme engine resolves theme_id + brand_kit into concrete styles
4. Layout engine positions all elements using constraint solver
5. PPTX/Slides renderer produces output
6. QA pipeline validates, auto-fixes, scores
7. Upload to R2, return download URL + QA score

**NL generation flow (always async):**
1. Client POSTs natural language prompt to /v1/generate
2. FastAPI returns 202 with job_id and SSE URL
3. Content worker runs 4-step LLM pipeline: intent -> outline -> expand -> refine
4. Pipeline produces validated IR
5. Same rendering path as structured flow
6. SSE events stream progress: "parsing", "outlining", "writing", "rendering", "qa"
7. Final SSE event: complete with download_url, quality_score, credits_used
8. Webhook fired if configured

## Patterns to Follow

### Pattern 1: IR as Single Source of Truth

**What:** Every operation (create, modify, retheme, batch) works on the IR level. Renderers are pure functions from IR to output.

**When:** Always. This is the architectural backbone.

**Why:** Deterministic output (same IR = same visual), format-agnostic (IR renders to PPTX or Slides), composable operations (merge/split/reorder at IR level).

```python
# The IR schema drives everything
class Presentation(BaseModel):
    metadata: PresentationMetadata
    brand_kit: BrandKit | None = None
    theme: str  # theme_id
    slides: list[Slide]
    generation_options: GenerationOptions | None = None

class Slide(BaseModel):
    slide_type: SlideType  # enum of 32 types
    layout_hint: LayoutHint | None = None
    elements: list[Element]
    speaker_notes: str | None = None

class Element(BaseModel):
    type: ElementType
    position: Position | None = None  # Layout engine fills this
    style_overrides: dict | None = None  # Theme fills defaults
    content: dict  # Type-specific payload
```

### Pattern 2: Theme Deep Merge with Protected Properties

**What:** Brand kit overlays merge on top of theme defaults, but certain properties (grid system, typography scale ratios, minimum margins) are protected.

**When:** Every render that includes a brand_kit.

**Why:** Prevents users from breaking layout integrity by overriding structural constraints. "Your colors, our layout intelligence."

```python
PROTECTED_KEYS = {"grid", "typography_scale", "min_margins", "min_font_sizes"}

def resolve_theme(theme_id: str, brand_kit: BrandKit | None) -> ResolvedTheme:
    base = theme_registry.get(theme_id)
    if not brand_kit:
        return base
    return deep_merge(base, brand_kit, protected=PROTECTED_KEYS)
```

### Pattern 3: Async Worker with SSE Progress

**What:** Long-running tasks (NL generation, large renders) run in ARQ workers. Progress is published to Redis pub/sub. FastAPI SSE endpoint subscribes and streams to client.

**When:** Any operation taking >3 seconds.

```python
# Worker publishes progress
async def content_worker(ctx, job_id: str, prompt: str):
    await publish_progress(job_id, "parsing", 0.1)
    intent = await parse_intent(prompt)
    await publish_progress(job_id, "outlining", 0.3)
    outline = await generate_outline(intent)
    # ... etc

# FastAPI streams progress
@app.get("/v1/jobs/{job_id}/events")
async def stream_events(job_id: str):
    async def event_generator():
        async for event in subscribe_progress(job_id):
            yield ServerSentEvent(data=event.json())
    return EventSourceResponse(event_generator())
```

### Pattern 4: Idempotent Operations with Request ID

**What:** Every generation/render request accepts an optional `request_id`. If the same request_id is seen again, return the cached result instead of re-processing.

**When:** All mutation endpoints.

**Why:** Agents retry on network failures. Without idempotency, retries produce duplicate charges and duplicate files.

### Pattern 5: Repository Pattern for Database Access

**What:** Database access goes through repository classes, never raw SQL in route handlers.

**When:** All database operations.

**Why:** Testability (mock repositories), separation of concerns, consistent transaction management.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Renderer Calling LLMs

**What:** Having the PPTX renderer call an LLM to "decide" layout or content.

**Why bad:** Breaks determinism (same IR should produce same output), makes rendering slow and expensive, couples rendering to network availability.

**Instead:** All intelligence happens in the content pipeline (before IR is produced) or the layout engine (deterministic constraint solving). Renderers are pure functions.

### Anti-Pattern 2: Template-Based Layout

**What:** Fixed slide templates where content is injected into predefined positions.

**Why bad:** Templates break when content volume varies. 3 bullets look fine but 12 bullets overflow. Different text lengths cause misalignment. Maintenance nightmare as each slide type x theme = an explosion of templates (32 types x 15 themes = 480 templates).

**Instead:** Constraint-based layout where the solver adapts positions to content. One layout algorithm handles all themes.

### Anti-Pattern 3: Synchronous LLM Calls in Request Handlers

**What:** Calling LLMs directly in FastAPI route handlers (blocking the event loop or using sync calls).

**Why bad:** LLM calls take 5-25 seconds. Blocking the event loop means no other requests are served. Even async LLM calls in the request handler tie up the connection for too long.

**Instead:** Queue LLM work to ARQ workers. Return 202 immediately with job_id. Stream progress via SSE.

### Anti-Pattern 4: Storing Files in PostgreSQL

**What:** Storing generated PPTX files as BYTEA columns in PostgreSQL.

**Why bad:** Bloats database size, slows backups, poor download performance, can't leverage CDN.

**Instead:** Store files in R2/S3. Store the download URL and metadata in PostgreSQL.

### Anti-Pattern 5: Shared Mutable State Between Workers

**What:** Workers modifying shared Python objects or using global state.

**Why bad:** ARQ workers run in separate processes. Shared state leads to race conditions and data corruption.

**Instead:** Workers communicate through Redis (pub/sub for progress, queue for tasks) and PostgreSQL (job status, results). Each worker is stateless.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| API requests | Single FastAPI instance | 2-4 instances behind load balancer | Auto-scaling ECS/Cloud Run |
| Rendering workers | 2 ARQ workers | 4-16 workers, auto-scale on queue depth | K8s HPA on queue metrics |
| LLM calls | Direct to providers | Rate limiting per API key | Provider load balancing, fallback chains |
| File storage | Single R2 bucket | Single R2 bucket (R2 scales) | Multi-region R2 with CDN |
| Database | Neon free tier | Neon Pro or AWS RDS | Read replicas, connection pooling |
| Redis | Upstash free tier | Upstash Pro or ElastiCache | Redis Cluster for pub/sub scale |
| Slide complexity | No concern | Cache popular theme resolves | Pre-compute layout templates for common patterns |

**Key scaling insight:** The bottleneck is rendering workers, not the API layer. A 50-slide deck with charts takes 3-8 seconds to render. Scaling means adding more workers, not more API instances. ARQ's Redis-backed queue handles this naturally -- add workers and they pull from the same queue.

## Sources

- [FastAPI 2026 architecture](https://nerdleveltech.com/building-lightning-fast-ai-backends-with-fastapi-2026-edition) - Production patterns
- [ARQ documentation](https://arq-docs.helpmanual.io/) - Async worker patterns
- [SQLAlchemy 2.0 asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - Async database patterns
- [Cassowary constraint solving](https://cassowary.readthedocs.io/en/latest/topics/theory.html) - Layout algorithm theory
- [FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/) - Native SSE support
- [Cloudflare R2 boto3](https://developers.cloudflare.com/r2/examples/aws/boto3/) - S3-compatible storage
- [Google Slides API batchUpdate](https://developers.google.com/workspace/slides/api/quickstart/python) - Slides rendering approach
