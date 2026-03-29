# Phase 8 Research: TypeScript SDK + Billing + Launch

**Researched:** 2026-03-26
**Phase:** 08-typescript-sdk-billing-launch
**Requirements:** SDK-01..05, BILL-01..06, API-05..07, INFRA-05

---

## 1. TypeScript SDK Generation from OpenAPI

### Tool: @hey-api/openapi-ts (from STACK.md)

Generates typed TypeScript client from FastAPI's auto-generated OpenAPI 3.1 spec.

**Setup:**
```bash
npx @hey-api/openapi-ts \
  --input http://localhost:8000/openapi.json \
  --output src/generated \
  --client fetch \
  --schemas zod
```

**What it generates:**
- TypeScript interfaces for every Pydantic model (Presentation, Slide types, Element types)
- Typed HTTP client methods for every endpoint
- Zod schemas for runtime validation
- Proper discriminated union types from Pydantic's discriminated unions

**Key config options:**
- `--client fetch`: Uses native fetch (no axios dependency, works in Node + browser)
- `--schemas zod`: Generates Zod schemas alongside types for runtime validation
- `--enums javascript`: Generates JS enums instead of string unions (more ergonomic)

**SDK Architecture:**
```
sdk/
  src/
    generated/      -- Auto-generated from OpenAPI (never edit)
    client.ts       -- DeckForge main client class
    builder/        -- Fluent builder API
      presentation.ts
      slide.ts
      elements.ts
    streaming.ts    -- SSE streaming helper
    types.ts        -- Re-exported types from generated
  package.json
  tsconfig.json
  tsup.config.ts
```

### Generation Workflow
1. Export OpenAPI spec from running FastAPI: `curl http://localhost:8000/openapi.json > openapi.json`
2. Run @hey-api/openapi-ts to generate typed client
3. Hand-write the fluent builder layer wrapping the generated client
4. Build with tsup (ESM + CJS dual output)

---

## 2. Fluent Builder Pattern in TypeScript

### Design Goal
Developers should be able to construct presentations naturally:

```typescript
const deck = await df.presentations
  .create("Q3 Financial Review")
  .theme("executive-dark")
  .addSlide(Slide.titleSlide({
    title: "Q3 2026 Financial Review",
    subtitle: "Board of Directors Meeting"
  }))
  .addSlide(Slide.bullets({
    title: "Key Highlights",
    items: ["Revenue up 23% YoY", "EBITDA margin expanded 200bps"]
  }))
  .addSlide(Slide.chart({
    title: "Revenue Trend",
    chart: Chart.line({ series: [...] })
  }))
  .render();
```

### Implementation Pattern: Immutable Builder with Method Chaining

```typescript
class PresentationBuilder {
  private readonly _ir: Partial<PresentationIR>;

  private constructor(ir: Partial<PresentationIR>) {
    this._ir = ir;
  }

  static create(title: string): PresentationBuilder {
    return new PresentationBuilder({
      schema_version: "1.0",
      metadata: { title, purpose: "general", audience: "general" },
      slides: [],
      theme: "executive-dark",
    });
  }

  theme(themeId: string): PresentationBuilder {
    return new PresentationBuilder({ ...this._ir, theme: themeId });
  }

  addSlide(slide: SlideInput): PresentationBuilder {
    return new PresentationBuilder({
      ...this._ir,
      slides: [...(this._ir.slides || []), slide],
    });
  }

  async render(client: DeckForgeClient): Promise<RenderResult> {
    const ir = this.build(); // Validates and returns full IR
    return client.render(ir);
  }

  build(): PresentationIR {
    // Validate required fields, return typed IR
    ...
  }
}
```

**Key design decisions:**
- Immutable: each method returns a new builder (safe to fork)
- Type-safe: `addSlide()` accepts `SlideInput` which is a discriminated union
- Lazy: no HTTP call until `.render()` or `.generate()`
- Composable: builders can be stored, passed around, and extended

### Slide Helper Factory

```typescript
const Slide = {
  titleSlide: (opts: TitleSlideInput) => ({ slide_type: "title" as const, ...opts }),
  bullets: (opts: BulletSlideInput) => ({ slide_type: "bullets" as const, ...opts }),
  chart: (opts: ChartSlideInput) => ({ slide_type: "chart" as const, ...opts }),
  table: (opts: TableSlideInput) => ({ slide_type: "table" as const, ...opts }),
  // ... all 32 slide types
};
```

---

## 3. SSE Client in TypeScript

### Native EventSource API

For browser environments, the built-in `EventSource` API works directly:

```typescript
class StreamingHelper {
  async *streamGeneration(jobId: string): AsyncGenerator<ProgressEvent> {
    const url = `${this.baseUrl}/v1/jobs/${jobId}/stream`;

    // Use fetch + ReadableStream for more control than EventSource
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${this.apiKey}` },
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = JSON.parse(line.slice(6));
          yield data as ProgressEvent;
        }
      }
    }
  }
}
```

**Why fetch + ReadableStream over EventSource:**
- EventSource does not support custom headers (no Authorization header)
- EventSource only supports GET (DeckForge SSE might need POST context)
- fetch + ReadableStream gives full control over parsing and reconnection
- Works in both Node.js (18+) and browsers

### SDK Usage Pattern
```typescript
const stream = df.generate.stream("Create a Q3 financial review...");

for await (const event of stream) {
  console.log(`${event.stage}: ${event.progress * 100}%`);
  if (event.stage === "complete") {
    console.log("Download:", event.file_url);
  }
}
```

---

## 4. Stripe Billing -- Subscriptions, Metered Usage, Credits

### Tier Configuration

| Tier | Price | Credits/mo | Overage Rate |
|------|-------|------------|--------------|
| Starter | $0 | 50 | $0.50/credit |
| Pro | $79/mo | 500 | $0.30/credit |
| Enterprise | Custom | Custom | Volume pricing |

### Stripe Product/Price Setup

```python
# One-time setup (admin script or manual in Stripe Dashboard)
starter_product = stripe.Product.create(name="DeckForge Starter")
pro_product = stripe.Product.create(name="DeckForge Pro")

# Pro subscription price
pro_price = stripe.Price.create(
    product=pro_product.id,
    unit_amount=7900,  # $79.00
    currency="usd",
    recurring={"interval": "month"},
)

# Metered overage price (usage-based)
overage_meter = stripe.billing.Meter.create(
    display_name="DeckForge Credits",
    event_name="deckforge_credit_usage",
    default_aggregation={"formula": "sum"},
)

starter_overage_price = stripe.Price.create(
    product=starter_product.id,
    currency="usd",
    billing_scheme="per_unit",
    unit_amount=50,  # $0.50
    recurring={"interval": "month", "meter": overage_meter.id, "usage_type": "metered"},
)
```

### Stripe Billing Credits (Native Feature)

Stripe's Billing Credits feature (launched 2025) handles the credit ledger natively:

```python
# Grant credits on subscription activation
stripe.billing.CreditGrant.create(
    customer=customer_id,
    amount={"type": "monetary", "monetary": {"value": 5000, "currency": "usd"}},
    # 500 credits at $0.10 each = $50 worth
    category="paid",
    effective_at=now,
    expires_at=end_of_month,
)

# Credits are automatically consumed by metered usage
# Overage charges only kick in when credit balance reaches 0
```

**This eliminates the need for a custom credit ledger.** Stripe tracks credit balance, consumption, and overage natively.

---

## 5. Credit Reservation Pattern (Hold -> Deduct -> Release)

### Why Reservation?
Prevent over-consumption: a user with 5 remaining credits should not be able to start 10 concurrent renders that each cost 1 credit.

### Implementation: Optimistic Locking with DB Counter

```python
class CreditReservation:
    """Reserve credits before work, deduct on completion, release on failure."""

    async def reserve(self, api_key_id: uuid.UUID, estimated_credits: int) -> ReservationToken:
        """Atomically reserve credits. Raises InsufficientCredits if balance too low."""
        async with self.db.begin():
            usage = await self.get_usage(api_key_id)
            available = usage.credit_limit - usage.used - usage.reserved
            if available < estimated_credits:
                raise InsufficientCreditsError(available=available, requested=estimated_credits)

            token = ReservationToken(id=uuid.uuid4(), amount=estimated_credits)
            usage.reserved += estimated_credits
            await self.save_reservation(token)
            return token

    async def deduct(self, token: ReservationToken, actual_credits: int) -> None:
        """Convert reservation to actual usage. Release excess."""
        async with self.db.begin():
            usage = await self.get_usage(token.api_key_id)
            usage.reserved -= token.amount
            usage.used += actual_credits
            await self.mark_reservation_complete(token)
            # Report to Stripe meter
            stripe.billing.MeterEvent.create(
                event_name="deckforge_credit_usage",
                payload={"value": str(actual_credits), "stripe_customer_id": customer_id},
            )

    async def release(self, token: ReservationToken) -> None:
        """Release reserved credits (job failed/cancelled)."""
        async with self.db.begin():
            usage = await self.get_usage(token.api_key_id)
            usage.reserved -= token.amount
            await self.mark_reservation_cancelled(token)
```

### Database Model
```python
class UsageRecord(Base):
    __tablename__ = "usage_records"
    id: Mapped[uuid.UUID]
    api_key_id: Mapped[uuid.UUID]
    period_start: Mapped[datetime]  # Monthly billing period
    credit_limit: Mapped[int]       # From tier (50, 500, custom)
    used: Mapped[int] = 0
    reserved: Mapped[int] = 0

class CreditReservation(Base):
    __tablename__ = "credit_reservations"
    id: Mapped[uuid.UUID]
    api_key_id: Mapped[uuid.UUID]
    amount: Mapped[int]
    status: Mapped[str]  # reserved, completed, cancelled
```

---

## 6. Discovery Endpoints Design

### GET /v1/themes

```json
{
  "themes": [
    {
      "id": "executive-dark",
      "name": "Executive Dark",
      "description": "Dark professional theme for board presentations",
      "version": "1.0",
      "colors": {"primary": "#0A1E3D", "accent": "#C7A94F", "background": "#1A1A2E"},
      "preview_url": "/v1/themes/executive-dark/preview"
    }
  ]
}
```

**Implementation:** Wraps `ThemeRegistry.list_themes()` (already exists) with additional color preview data.

### GET /v1/slide-types

```json
{
  "slide_types": [
    {
      "id": "title",
      "name": "Title Slide",
      "description": "Opening slide with title and subtitle",
      "category": "universal",
      "example_ir": { "slide_type": "title", "elements": [...] },
      "required_elements": ["heading"],
      "optional_elements": ["subheading", "image"]
    }
  ]
}
```

**Implementation:** Static registry derived from IR schema discriminated union types. Example IR is a minimal valid payload for each type.

### GET /v1/capabilities

```json
{
  "api_version": "1.0",
  "max_slides_sync": 10,
  "max_slides_async": 200,
  "supported_output_formats": ["pptx", "gslides"],
  "supported_chart_types": ["bar", "line", "pie", ...],
  "rate_limits": {"starter": 10, "pro": 60, "enterprise": "custom"},
  "features": {
    "streaming": true,
    "webhooks": true,
    "batch": true,
    "finance_slides": true
  }
}
```

---

## 7. Railway/Fly.io Deployment Configuration

### Fly.io (Recommended for DeckForge)

Fly.io advantages over Railway for this workload:
- Process groups: API and workers in same deployment but different process groups
- Built-in Redis (Upstash) and Postgres (Fly Postgres)
- Global edge deployment for API latency
- Docker-native (DeckForge already has Dockerfile)

**fly.toml:**
```toml
app = "deckforge-api"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  DECKFORGE_ENV = "production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    hard_limit = 250
    soft_limit = 200

[[vm]]
  memory = "1gb"
  cpu_kind = "shared"
  cpus = 2
```

**Worker process group (separate fly.toml or process group):**
```toml
[processes]
  api = "uvicorn deckforge.main:app --host 0.0.0.0 --port 8000"
  worker = "python -m deckforge.workers.run"
```

### Railway Alternative

```json
{
  "build": { "dockerfilePath": "Dockerfile" },
  "deploy": {
    "startCommand": "uvicorn deckforge.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/v1/health",
    "healthcheckTimeout": 10
  }
}
```

Railway uses separate services for API and workers (each deployed from the same repo with different start commands).

### Dockerfile Enhancement for Production

The existing Dockerfile needs:
1. Multi-stage build (builder + runtime)
2. Non-root user
3. Health check instruction
4. Production dependencies only

---

## 8. npm Package Publishing Workflow

### Package Configuration

```json
{
  "name": "@deckforge/sdk",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.cjs",
  "module": "dist/index.js",
  "types": "dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist"],
  "scripts": {
    "generate": "openapi-ts --input openapi.json --output src/generated",
    "build": "tsup src/index.ts --format esm,cjs --dts",
    "test": "vitest run",
    "prepublishOnly": "npm run build"
  }
}
```

### Publishing Steps
1. Generate types from latest OpenAPI spec
2. Run tests
3. Build with tsup
4. `npm publish --access public`

### CI Workflow (future)
```yaml
# .github/workflows/sdk-publish.yml
on:
  release:
    types: [published]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm test && npm run build
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## Plan Architecture

### Plan 08-01 (Wave 1): TypeScript SDK
**Requirements:** SDK-01, SDK-02, SDK-03, SDK-04, SDK-05

Files:
- `sdk/package.json` -- Package config
- `sdk/tsconfig.json` -- TypeScript config
- `sdk/tsup.config.ts` -- Build config
- `sdk/src/generated/` -- Auto-generated from OpenAPI
- `sdk/src/client.ts` -- DeckForge client class
- `sdk/src/builder/presentation.ts` -- Fluent builder
- `sdk/src/builder/slide.ts` -- Slide factory helpers
- `sdk/src/builder/elements.ts` -- Element factory helpers
- `sdk/src/streaming.ts` -- SSE streaming helper
- `sdk/src/types.ts` -- Re-exported types
- `sdk/src/index.ts` -- Public API entrypoint
- `sdk/tests/` -- Vitest tests

### Plan 08-02 (Wave 1): Stripe Billing
**Requirements:** BILL-01, BILL-02, BILL-03, BILL-04, BILL-05, BILL-06

Files:
- `src/deckforge/billing/__init__.py`
- `src/deckforge/billing/tiers.py` -- Tier definitions
- `src/deckforge/billing/credits.py` -- Credit reservation + deduction
- `src/deckforge/billing/stripe_client.py` -- Stripe API wrapper
- `src/deckforge/billing/webhooks.py` -- Stripe webhook handler
- `src/deckforge/db/models/usage.py` -- UsageRecord + CreditReservation models
- `src/deckforge/db/repositories/usage.py` -- Usage repo
- `src/deckforge/api/routes/billing.py` -- Usage dashboard endpoint
- `src/deckforge/api/middleware/credits.py` -- Credit check middleware
- Alembic migration for usage_records and credit_reservations tables

### Plan 08-03 (Wave 2): Discovery + Deployment + Launch
**Requirements:** API-05, API-06, API-07, INFRA-05

Files:
- `src/deckforge/api/routes/discovery.py` -- /v1/themes, /v1/slide-types, /v1/capabilities
- `src/deckforge/services/slide_type_registry.py` -- Slide type metadata + examples
- `fly.toml` -- Fly.io deployment config
- `Dockerfile` -- Production-optimized multi-stage build
- `Procfile` -- Process types (api, worker)
- `.dockerignore` -- Production exclusions

---

## Sources

- @hey-api/openapi-ts: https://github.com/hey-api/openapi-ts
- FastAPI SDK generation: https://fastapi.tiangolo.com/advanced/generate-clients/
- Stripe Billing Credits: https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits/implementation-guide
- Stripe Meters API: https://docs.stripe.com/api/billing/meter
- Stripe Webhook Signatures: https://docs.stripe.com/webhooks/signatures
- Fly.io process groups: https://fly.io/docs/apps/processes/
- Fly.io Dockerfile deployment: https://fly.io/docs/languages-and-frameworks/dockerfile/
- tsup bundler: https://tsup.egoist.dev/
- npm publishing: https://docs.npmjs.com/creating-and-publishing-scoped-public-packages
- Existing codebase: ThemeRegistry.list_themes() in src/deckforge/themes/registry.py
