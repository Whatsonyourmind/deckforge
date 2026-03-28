# Domain Pitfalls

**Domain:** API-first AI slide generation platform (DeckForge)
**Researched:** 2026-03-26

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Text Overflow in PPTX Rendering

**What goes wrong:** Text is placed in a text box sized for a theme's default content, but actual content is longer. In PowerPoint, text silently overflows or gets clipped -- there is no automatic reflow. The deck looks broken.

**Why it happens:** python-pptx does not automatically resize text boxes or adjust font sizes when content overflows. It writes exactly what you tell it to write at exactly the size you specify. Unlike HTML/CSS, there is no overflow:hidden or text-wrap behavior.

**Consequences:** "Executive-ready" brand promise is broken. Clipped text is the number one quality complaint in programmatic slide generation.

**Prevention:**
- Text measurement using Pillow (ImageFont) before placing text
- Iterative font-size reduction (floor at 12pt) when text exceeds bounding box
- Slide splitting when content cannot fit at minimum font size
- QA pass 2 (Text Quality) catches remaining overflow

**Detection:** QA pipeline measures text bounding boxes post-render. Any text where measured height exceeds box height is flagged.

### Pitfall 2: LiteLLM Supply Chain Compromise

**What goes wrong:** LiteLLM versions 1.82.7 and 1.82.8 (March 2026) contained credential-stealing malware via a compromised PyPI account. Installing these versions exfiltrates AWS keys, GCP credentials, SSH keys, and crypto wallets.

**Why it happens:** Supply chain attacks on popular packages. The LiteLLM maintainer account was compromised through a trojanized security scanner (Trivy).

**Consequences:** Complete credential exposure. Requires full key rotation across all services.

**Prevention:**
- Pin `litellm==1.82.6` exactly in pyproject.toml
- Use `pip install --require-hashes` in CI/CD
- Run pip-audit in CI to detect known vulnerabilities
- Maintain a thin custom LLM adapter as escape hatch if LiteLLM trust does not recover
- Monitor https://docs.litellm.ai/blog/security-update-march-2026

**Detection:** pip-audit, Safety CLI, or Snyk vulnerability scanning in CI.

### Pitfall 3: Constraint-Based Layout is Harder Than It Looks

**What goes wrong:** Building a layout engine that adapts to variable content volume is a multi-month R&D effort, not a weekend project. Teams underestimate this and either ship broken layouts or fall back to fixed templates.

**Why it happens:** Constraint-based layout requires: text measurement (font metrics), grid system math, constraint generation (converting slide type + content into kiwisolver constraints), iterative refinement (overflow handling, sparse content scaling), and extensive testing across all 32 slide types x 15 themes.

**Consequences:** Without adaptive layout, the product is just a "template filler" -- competitors already do this. The layout engine IS the moat.

**Prevention:**
- Start with a simpler grid-based positioning system for MVP
- Build constraint solving incrementally (start with single-column, then multi-column, then complex)
- Prototype the hardest cases first (comp tables with 15 rows, bullet lists with 3 vs 12 items)
- Study iOS Auto Layout and CSS Grid spec for constraint modeling patterns
- Budget 3-4 weeks of dedicated layout engine development

**Detection:** Visual regression testing -- render the same IR with different content volumes and compare layouts.

### Pitfall 4: Google Slides Chart Embedding is Not Straightforward

**What goes wrong:** The Google Slides API does not support creating charts directly. You must create a Google Sheets spreadsheet, add the chart data and chart there, then embed the Sheets chart into Slides via `createSheetsChart`. This is a multi-API workflow with its own auth, rate limits, and failure modes.

**Why it happens:** Google Slides charts are backed by Sheets data. There is no chart-creation API in Slides alone.

**Consequences:** Each presentation with charts requires creating (and potentially cleaning up) a temporary Sheets spreadsheet. Rate limits on Sheets API can throttle chart creation. Orphaned spreadsheets accumulate if cleanup fails.

**Prevention:**
- Create a dedicated service account for Sheets operations
- Implement retry logic with exponential backoff for Sheets API calls
- Schedule cleanup of temporary Sheets (cron job or TTL-based)
- Batch chart data into a single Sheets workbook (one sheet per chart) to minimize API calls
- Fall back to static chart images if Sheets API is unavailable

**Detection:** Monitor Sheets API quota usage. Alert on orphaned spreadsheets older than 24 hours.

### Pitfall 5: PPTX Chart Type Limitations in python-pptx

**What goes wrong:** python-pptx supports 16 distinct chart XML element types, which cover common chart types (bar, line, pie, scatter, area, radar, bubble, combo). However, financial-grade charts like waterfall, funnel, treemap, and sensitivity tables are NOT native python-pptx chart types. They must be built from lower-level primitives.

**Why it happens:** PowerPoint's native waterfall chart type was added in Office 2016, but python-pptx's chart implementation predates this and has not been updated.

**Consequences:** Finance vertical charts (waterfall, football field, sensitivity table) require either: (a) building from stacked bar charts with invisible series (complex, brittle), or (b) embedding as static images (not editable in PowerPoint).

**Prevention:**
- For waterfall: Build from stacked bar with invisible series + lxml for color customization. This is a known pattern.
- For football field / sensitivity: Use static image embedding (Plotly render). These chart types are complex enough that editability is not expected.
- For comp tables: Use python-pptx Table element, not charts. Tables handle this better.
- Test all finance chart types early in development to identify which approach works for each

**Detection:** Manual visual review of all 9 finance slide types. Automated comparison against reference renders.

## Moderate Pitfalls

### Pitfall 6: Font Availability in Docker/Production

**What goes wrong:** Presentation themes specify fonts (e.g., "Montserrat", "Garamond", "DM Sans") that are not installed in the production Docker container. python-pptx embeds font references in the PPTX, but if the font metrics are wrong (because measurement used a fallback font), text sizing is incorrect.

**Prevention:**
- Bundle all theme fonts in the Docker image (Google Fonts are free, others need licenses)
- Use Pillow's ImageFont.truetype() with the exact font file for text measurement
- Fall back to a known-available font (Liberation Sans, DejaVu Sans) if a theme font is missing
- Include font availability check in the health endpoint

### Pitfall 7: Redis as Single Point of Failure

**What goes wrong:** Redis handles task queue (ARQ), rate limiting, SSE pub/sub, and caching. If Redis goes down, everything stops.

**Prevention:**
- Use managed Redis (Upstash for MVP, ElastiCache/Memorystore for production) with automatic failover
- ARQ has built-in retry logic for Redis disconnections
- Rate limiting can degrade gracefully (allow requests when Redis is unreachable, log warning)
- For SSE, implement polling fallback (client polls /v1/jobs/{id}/status instead of streaming)

### Pitfall 8: Pydantic IR Schema Versioning

**What goes wrong:** The IR schema evolves (new slide types, new element properties). Stored IR from older versions becomes invalid against the current schema. APIs break for clients sending old-format IR.

**Prevention:**
- Version the IR schema (v1, v2) and maintain migration functions
- API endpoints include version prefix (/v1/render, /v2/render)
- Store IR with a schema_version field
- Write backward-compatible Pydantic validators (Optional fields with defaults for new properties)
- Never remove fields from the IR -- deprecate and ignore

### Pitfall 9: LLM Output Non-Determinism

**What goes wrong:** The NL generation pipeline produces different IR for the same prompt on every call, even with temperature=0. This makes testing hard and creates inconsistent user experiences.

**Prevention:**
- Structured output (Pydantic models via LLM tool/function calling) constrains variability
- Pin specific model versions (e.g., claude-sonnet-4-20250514, not claude-sonnet-4)
- Use seed parameter where supported (OpenAI supports, Anthropic does not)
- Accept that NL generation is inherently non-deterministic; the structured /v1/render endpoint is the deterministic path
- Integration tests for NL pipeline test structure (slide count, types) not exact content

### Pitfall 10: Async Worker Memory Leaks

**What goes wrong:** ARQ workers processing many rendering jobs accumulate memory over time, especially when handling large presentations with many images.

**Prevention:**
- Set ARQ worker max_jobs and restart workers after N jobs
- Use memory profiling (memray) during development
- Ensure python-pptx Presentation objects are explicitly closed/garbage collected
- Avoid storing large byte arrays (PPTX content) in Redis -- upload to R2 immediately
- Set Docker container memory limits to force restart on leak

## Minor Pitfalls

### Pitfall 11: SSE Connection Limits

**What goes wrong:** Each SSE connection holds an HTTP connection open. Clients that do not disconnect (abandoned tabs, crashed agents) accumulate, eventually exhausting server connections.

**Prevention:** sse-starlette has automatic disconnect detection. Set a server-side timeout (60s for generation, configurable). Include timeout info in the SSE stream.

### Pitfall 12: OpenAPI Schema Size

**What goes wrong:** With 32 slide types, 20+ chart types, and deeply nested IR schema, the OpenAPI JSON becomes very large (1MB+), slowing down docs rendering and SDK generation.

**Prevention:** Use discriminated unions in Pydantic to reduce schema size. Generate separate OpenAPI schemas for different API sections. Consider separate "IR Reference" documentation outside OpenAPI.

### Pitfall 13: Stripe Webhook Reliability

**What goes wrong:** Stripe webhooks are "at least once" delivery. Processing a payment webhook twice can double-credit a user.

**Prevention:** Idempotent webhook processing using Stripe event IDs. Check if event was already processed before applying credit changes.

### Pitfall 14: Google OAuth Token Management

**What goes wrong:** OAuth tokens for Google Slides access expire after 1 hour. Long-running jobs or batch operations fail mid-execution when the token expires.

**Prevention:** Implement token refresh logic in the Google Slides renderer. Use service accounts (which auto-refresh) for platform-owned operations. For user-authorized operations, refresh tokens before job start if expiry is within 10 minutes.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| IR Schema Design | Schema too rigid or too permissive | Start with 10 core slide types, validate with real rendering, then expand |
| PPTX Rendering | Text overflow, font metrics | Text measurement before placement, iterative font reduction |
| Layout Engine | Underestimating complexity | Start simple (grid positioning), add constraints incrementally |
| Content Pipeline | LiteLLM security, LLM non-determinism | Pin version, structured output, test structure not content |
| Chart Engine | python-pptx chart type gaps | Test all finance charts early, decide native vs static per type |
| Google Slides | Chart embedding complexity, rate limits | Sheets-backed charts with retry, batch operations, cleanup jobs |
| QA Pipeline | False positives, slow execution | Tune thresholds iteratively, parallelize QA passes |
| SDK + Billing | OpenAPI schema bloat, webhook idempotency | Discriminated unions, event ID deduplication |

## Sources

- [python-pptx chart documentation](https://python-pptx.readthedocs.io/en/latest/user/charts.html) - Chart type limitations
- [LiteLLM Security Advisory](https://docs.litellm.ai/blog/security-update-march-2026) - Supply chain attack details
- [Kaleido v1 changes](https://plotly.com/python/static-image-generation-changes/) - Chrome dependency
- [ARQ documentation](https://arq-docs.helpmanual.io/) - Worker patterns and limitations
- [Google Slides API guide](https://www.flashdocs.com/post/google-slides-api-comprehensive-guide-for-developers) - API complexity
- [Stripe billing credits](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits/implementation-guide) - Credit system patterns
- [sse-starlette](https://github.com/sysid/sse-starlette) - SSE disconnect handling
- [Cassowary constraint theory](https://cassowary.readthedocs.io/en/latest/topics/theory.html) - Layout solver fundamentals
