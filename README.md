<p align="center">
  <h1 align="center">DeckForge</h1>
  <p align="center"><strong>API-first presentation generation for humans and AI agents</strong></p>
</p>

<p align="center">
  <a href="https://github.com/Whatsonyourmind/deckforge/actions/workflows/ci.yml"><img src="https://github.com/Whatsonyourmind/deckforge/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/npm/v/@deckforge/sdk?color=cb3837&logo=npm" alt="npm @deckforge/sdk">
  <img src="https://img.shields.io/badge/slides-32%20types-blueviolet" alt="32 slide types">
  <img src="https://img.shields.io/badge/themes-15-orange" alt="15 themes">
</p>

---

Executive-ready slides, one API call away. Send a JSON intermediate representation (IR) or a natural-language prompt and get back a `.pptx` file, Google Slides deck, or thumbnail PNG -- with professional layout, consistent branding, and verified quality.

## Features

- **32 slide types** -- title, agenda, bullet points, comparison, timeline, process flow, org chart, stats callout, table, chart, matrix, funnel, map, and more
- **9 finance-specific slides** -- DCF summary, comp table, waterfall chart, deal overview, returns analysis, capital structure, market landscape, risk matrix, investment thesis
- **24 chart types** -- bar, line, area, pie, donut, scatter, bubble, combo, waterfall, funnel, treemap, radar, tornado, football field, sensitivity table, heatmap, sankey, gantt, sunburst, and more
- **15 built-in themes** -- corporate-blue, executive-dark, finance-pro, modern-gradient, minimal-light, tech-neon, and 9 others (plus custom brand kits)
- **Native PPTX output** -- python-pptx rendering with element-level control, transitions, and chart embedding
- **Google Slides output** -- direct export via Google Slides API (OAuth flow included)
- **AI content generation** -- natural-language to slides via Claude, OpenAI, Gemini, or Ollama (4-stage pipeline: intent, outline, expand, refine)
- **5-pass QA pipeline** -- automated quality checks with auto-fix engine for contrast, overflow, alignment, and more
- **Constraint-based layout** -- kiwisolver constraint solver, 12-column grid, adaptive overflow (font reduce, reflow, split)
- **MCP server** -- 6 tools for AI agent integration (render, generate, themes, slide types, estimate, preview)
- **x402 machine payments** -- per-call USDC pricing on Base L2 for autonomous AI agents
- **Stripe billing** -- subscription tiers (Starter free, Pro $79/mo, Enterprise custom) with credit system
- **TypeScript SDK** -- `@deckforge/sdk` with fluent builder pattern, full type safety, SSE streaming

## Quick Start

Get from zero to your first rendered deck in under 5 minutes.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/Whatsonyourmind/deckforge && cd deckforge

# 2. Copy environment config (works out of the box for local dev)
cp .env.example .env

# 3. Start all services (API, workers, PostgreSQL, Redis, MinIO)
docker compose up -d

# 4. Initialize the database (runs migrations, seeds test user + API key)
bash scripts/bootstrap-db.sh

# 5. Verify the API is running
curl http://localhost:8000/v1/health
# => {"status":"healthy"}
```

The bootstrap script outputs a test API key (`dk_test_...`). Save it for the examples below.

## API Examples

### Render a deck from IR

```bash
curl -X POST http://localhost:8000/v1/render \
  -H "Authorization: Bearer dk_test_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q4 Board Update",
    "theme": "corporate-blue",
    "slides": [
      {
        "slide_type": "title_slide",
        "elements": [
          {"type": "title", "content": "Q4 2026 Board Update"},
          {"type": "subtitle", "content": "Acme Corp -- Confidential"}
        ]
      },
      {
        "slide_type": "stats_callout",
        "elements": [
          {"type": "title", "content": "Key Metrics"},
          {"type": "metric", "content": "$4.2M", "label": "ARR"},
          {"type": "metric", "content": "142%", "label": "YoY Growth"},
          {"type": "metric", "content": "94%", "label": "Retention"}
        ]
      }
    ]
  }' \
  --output board-update.pptx
```

### Generate a deck from natural language

```bash
curl -X POST http://localhost:8000/v1/generate \
  -H "Authorization: Bearer dk_test_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a 10-slide pitch deck for a B2B SaaS startup in the cybersecurity space, Series A, $2M ARR",
    "theme": "executive-dark",
    "output_format": "pptx"
  }' \
  --output pitch-deck.pptx
```

> **Note:** The `/v1/generate` endpoint requires at least one LLM API key configured in `.env` (Anthropic, OpenAI, Gemini, or Ollama).

### Check available themes and slide types

```bash
# List all 15 themes
curl http://localhost:8000/v1/themes

# List all 32 slide types with example IR
curl http://localhost:8000/v1/slide-types

# Estimate credit cost before rendering
curl -X POST http://localhost:8000/v1/estimate \
  -H "Authorization: Bearer dk_test_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"slides": [{"slide_type": "title_slide"}, {"slide_type": "chart_slide"}]}'
```

## TypeScript SDK

Install from npm:

```bash
npm install @deckforge/sdk
```

Fluent builder with full type safety:

```typescript
import { DeckForge, Presentation, Slides } from "@deckforge/sdk";

const client = new DeckForge({ apiKey: "dk_test_YOUR_KEY_HERE" });

const deck = Presentation.create("Q4 Board Update", "corporate-blue")
  .addSlide(
    Slides.titleSlide({
      title: "Q4 2026 Board Update",
      subtitle: "Acme Corp -- Confidential",
    })
  )
  .addSlide(
    Slides.statsCallout({
      title: "Key Metrics",
      metrics: [
        { value: "$4.2M", label: "ARR" },
        { value: "142%", label: "YoY Growth" },
        { value: "94%", label: "Retention" },
      ],
    })
  );

const pptx = await client.render(deck);
// => Buffer containing .pptx file
```

Generate from a prompt with SSE streaming:

```typescript
const stream = client.generate({
  prompt: "Create a PE deal memo for a $500M LBO of a healthcare platform",
  theme: "finance-pro",
});

for await (const event of stream) {
  console.log(`${event.stage}: ${event.message}`);
}
// intent: Analyzing prompt for presentation structure...
// outline: Creating 12-slide deal memo outline...
// expand: Generating slide content...
// refine: Running QA pipeline (5 passes)...
// complete: Deck ready for download
```

## Architecture

```
                        +------------------+
                        |    Clients       |
                        |  (curl/SDK/MCP)  |
                        +--------+---------+
                                 |
                        +--------v---------+
                        |  FastAPI (uvicorn)|
                        |  /v1/* routes     |
                        |  Auth + Rate Limit|
                        |  Credit Billing   |
                        +--+-----+------+--+
                           |     |      |
               +-----------+     |      +----------+
               |                 |                  |
      +--------v------+  +------v--------+  +------v--------+
      | Content Worker |  | Render Worker |  |   Sync Path   |
      | (ARQ + Redis)  |  | (ARQ + Redis) |  | (< 10 slides) |
      | NL -> IR       |  | IR -> PPTX    |  | Direct return  |
      +--------+------+  +------+--------+  +------+--------+
               |                 |                  |
               v                 v                  v
      +--------+------+  +------+---------+  +-----+--------+
      | LLM Adapters  |  | PPTX Renderer  |  | Google Slides|
      | Claude/GPT/   |  | Layout Engine  |  | Renderer     |
      | Gemini/Ollama  |  | Theme Resolver |  | (OAuth)      |
      +---------------+  | Chart Renderer |  +--------------+
                          | QA Pipeline    |
                          +------+---------+
                                 |
                          +------v---------+
                          |    Storage     |
                          | MinIO (dev)    |
                          | R2/S3 (prod)   |
                          +----------------+

      +----------------+  +----------------+
      |   PostgreSQL   |  |     Redis      |
      |   Users, Keys  |  |  Queue, Cache  |
      |   Jobs, Decks  |  |  Rate Limits   |
      |   Billing      |  |  SSE Pub/Sub   |
      +----------------+  +----------------+
```

## API Routes

All routes are mounted under the `/v1` prefix. Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/v1/health` | GET | No | Health check |
| `/v1/render` | POST | API key | Render IR to PPTX/Google Slides |
| `/v1/generate` | POST | API key | Generate slides from natural language |
| `/v1/preview` | POST | API key | Generate thumbnail PNGs |
| `/v1/estimate` | POST | API key | Estimate credit cost |
| `/v1/jobs/{id}` | GET | API key | Check async job status |
| `/v1/themes` | GET | No | List available themes |
| `/v1/slide-types` | GET | No | List slide types with examples |
| `/v1/decks` | GET/POST/DELETE | API key | Deck CRUD operations |
| `/v1/batch` | POST | API key | Batch render multiple decks |
| `/v1/webhooks` | GET/POST/DELETE | API key | Manage webhook subscriptions |
| `/v1/billing/*` | Various | API key | Stripe subscription management |
| `/v1/pricing` | GET | No | Current pricing and tier info |
| `/v1/onboard/signup` | POST | No | Create account and API key |
| `/v1/analytics/*` | GET | Admin | Usage analytics and metrics |
| `/v1/auth/google/*` | GET | API key | Google OAuth flow for Slides |

## Environment Variables

All variables are prefixed with `DECKFORGE_`. See [`.env.example`](.env.example) for the complete reference with comments and example values.

| Variable | Default | Description |
|----------|---------|-------------|
| `DECKFORGE_DATABASE_URL` | `postgresql+psycopg://...localhost` | PostgreSQL connection string |
| `DECKFORGE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection (queue, cache, pub/sub) |
| `DECKFORGE_S3_ENDPOINT_URL` | `http://localhost:9000` | S3-compatible storage endpoint |
| `DECKFORGE_S3_ACCESS_KEY` | `minioadmin` | S3 access key (MinIO default for dev) |
| `DECKFORGE_S3_SECRET_KEY` | `minioadmin` | S3 secret key |
| `DECKFORGE_S3_BUCKET` | `deckforge` | S3 bucket name |
| `DECKFORGE_API_HOST` | `0.0.0.0` | API bind address |
| `DECKFORGE_API_PORT` | `8000` | API port |
| `DECKFORGE_DEBUG` | `true` | Debug mode (disable in production) |
| `DECKFORGE_ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `DECKFORGE_LLM_DEFAULT_PROVIDER` | `claude` | Default LLM for content generation |
| `DECKFORGE_LLM_FALLBACK_CHAIN` | `claude,openai,gemini` | LLM fallback order |
| `DECKFORGE_ANTHROPIC_API_KEY` | -- | Anthropic API key for Claude |
| `DECKFORGE_OPENAI_API_KEY` | -- | OpenAI API key |
| `DECKFORGE_GEMINI_API_KEY` | -- | Google Gemini API key |
| `DECKFORGE_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama local server URL |
| `DECKFORGE_STRIPE_SECRET_KEY` | -- | Stripe secret key |
| `DECKFORGE_STRIPE_WEBHOOK_SECRET` | -- | Stripe webhook signing secret |
| `DECKFORGE_STRIPE_STARTER_PRICE_ID` | -- | Stripe price ID for Starter tier |
| `DECKFORGE_STRIPE_PRO_PRICE_ID` | -- | Stripe price ID for Pro tier |
| `DECKFORGE_GOOGLE_CLIENT_ID` | -- | Google OAuth client ID (for Slides) |
| `DECKFORGE_GOOGLE_CLIENT_SECRET` | -- | Google OAuth client secret |
| `DECKFORGE_GOOGLE_REDIRECT_URI` | `http://localhost:8000/v1/auth/google/callback` | OAuth redirect URI |
| `DECKFORGE_UNKEY_ROOT_KEY` | -- | Unkey root key (production auth) |
| `DECKFORGE_UNKEY_API_ID` | -- | Unkey API ID |
| `DECKFORGE_X402_ENABLED` | `false` | Enable x402 USDC payments |
| `DECKFORGE_X402_WALLET_ADDRESS` | -- | USDC receiving wallet on Base |
| `DECKFORGE_X402_FACILITATOR_URL` | `https://x402.org/facilitator` | x402 facilitator endpoint |
| `DECKFORGE_X402_NETWORK` | `eip155:8453` | Base Mainnet chain ID |

## Deployment

### Fly.io (Recommended)

DeckForge ships with a production-ready `fly.toml` and multi-stage `Dockerfile`.

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login and launch
fly auth login
fly launch --name deckforge-api --region iad

# 3. Provision PostgreSQL
fly postgres create --name deckforge-db --region iad
fly postgres attach deckforge-db

# 4. Provision Redis (via Upstash or Fly Redis)
fly redis create --name deckforge-redis
# Copy the REDIS_URL from output

# 5. Set production secrets
fly secrets set \
  DECKFORGE_ENVIRONMENT=production \
  DECKFORGE_DEBUG=false \
  DECKFORGE_DATABASE_URL="postgres://..." \
  DECKFORGE_REDIS_URL="redis://..." \
  DECKFORGE_S3_ENDPOINT_URL="https://..." \
  DECKFORGE_S3_ACCESS_KEY="..." \
  DECKFORGE_S3_SECRET_KEY="..." \
  DECKFORGE_S3_BUCKET="deckforge" \
  DECKFORGE_STRIPE_SECRET_KEY="sk_live_..." \
  DECKFORGE_STRIPE_WEBHOOK_SECRET="whsec_..." \
  DECKFORGE_ANTHROPIC_API_KEY="sk-ant-..."

# 6. Deploy
fly deploy

# 7. Run database migrations
fly ssh console -C "alembic upgrade head"

# 8. Verify
curl https://deckforge-api.fly.dev/v1/health
```

**Fly.io configuration highlights:**

- 2 shared CPUs, 1 GB RAM per VM
- Auto-stop/start for cost efficiency (min 1 machine running)
- Forced HTTPS with concurrency limits (200 soft / 250 hard)
- Multi-process: `api` (uvicorn) + `worker` (ARQ)

### Docker Compose (Local Development)

```bash
# Start all 6 services
docker compose up -d

# Services:
#   api             - FastAPI + uvicorn (port 8000)
#   content-worker  - ARQ worker for NL-to-IR generation
#   render-worker   - ARQ worker for IR-to-PPTX rendering
#   postgres        - PostgreSQL 16 (port 5432)
#   redis           - Redis 7 (port 6379)
#   minio           - MinIO S3-compatible storage (port 9000, console 9001)

# Check service health
docker compose ps

# View API logs
docker compose logs -f api

# Tear down (preserves data volumes)
docker compose down

# Full reset (removes data)
docker compose down -v
```

### S3 Storage Options

| Environment | Provider | Config |
|-------------|----------|--------|
| Local dev | MinIO (via Docker Compose) | Default `.env.example` values |
| Production | Cloudflare R2 | Set `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` |
| Production | AWS S3 | Set `S3_ENDPOINT_URL` to AWS endpoint |
| Fly.io | Fly Tigris | `fly storage create`, auto-configured |

## Pricing

### Subscription Tiers

| Tier | Price | Credits/month | Rate Limit | Best For |
|------|-------|---------------|------------|----------|
| **Starter** | Free | 50 | 10 req/min | Evaluation, hobby projects |
| **Pro** | $79/month | 500 | 60 req/min | Teams, production apps |
| **Enterprise** | Custom | 10,000+ | 300 req/min | High-volume, overage allowed |

### Credit Cost

Each API call consumes credits based on complexity:
- **Simple render** (< 5 slides): 1 credit
- **Standard render** (5-20 slides): 2-3 credits
- **Complex render** (charts, finance slides): 3-5 credits
- **Content generation** (NL-to-IR): +2 credits (LLM usage)

### x402 Per-Call Pricing (AI Agents)

For autonomous AI agents that prefer pay-per-call over subscriptions:

| Endpoint | USDC Price | Network |
|----------|-----------|---------|
| `/v1/render` | $0.05 | Base L2 |
| `/v1/generate` | $0.15 | Base L2 |
| Metadata endpoints | Free | -- |

x402 payments bypass rate limiting (per-call payment is self-throttling).

## Demo Decks

Five production-quality demo IRs in [`demos/`](demos/):

| Demo | Slides | Theme | Use Case |
|------|--------|-------|----------|
| [McKinsey Strategy](demos/mckinsey-strategy/) | 12 | corporate-blue | Strategy consulting deck |
| [PE Deal Memo](demos/pe-deal-memo/) | 10 | finance-pro | Private equity investment committee |
| [Startup Pitch](demos/startup-pitch/) | 12 | modern-gradient | Series A fundraising |
| [Board Update](demos/board-update/) | 8 | executive-dark | Quarterly board meeting |
| [Product Launch](demos/product-launch/) | 10 | tech-neon | Product launch announcement |

Render any demo:

```bash
curl -X POST http://localhost:8000/v1/render \
  -H "Authorization: Bearer dk_test_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d @demos/mckinsey-strategy/ir.json \
  --output mckinsey-strategy.pptx
```

## Integrations

### MCP Server (AI Agents)

DeckForge includes a [Model Context Protocol](https://modelcontextprotocol.io/) server with 6 tools:

```json
{
  "mcpServers": {
    "deckforge": {
      "command": "python",
      "args": ["-m", "deckforge.mcp"]
    }
  }
}
```

Tools: `render`, `generate`, `themes`, `slide_types`, `estimate`, `preview`

### Agent Framework Support

- **LangChain** -- render + generate tool classes
- **CrewAI** -- unified tool with action parameter
- **AutoGen** -- plain function tools with `Annotated` types

See [`demos/`](demos/) for integration examples.

## Links

- [TypeScript SDK (`@deckforge/sdk`)](sdk/README.md)
- [API Docs (interactive)](http://localhost:8000/docs)
- [Landing Page](https://deckforge.dev)
- [GitHub Issues](https://github.com/Whatsonyourmind/deckforge/issues)

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run tests (`pytest` for Python, `cd sdk && npm test` for TypeScript)
4. Commit and push
5. Open a Pull Request

## License

[MIT](LICENSE)

---

<p align="center">
  <strong>DeckForge</strong> -- Executive-ready slides, one API call away.
</p>
