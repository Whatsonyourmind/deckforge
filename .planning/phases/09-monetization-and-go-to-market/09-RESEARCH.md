# Phase 9 Research: Monetization and Go-To-Market

**Conducted:** 2026-03-26
**Phase:** 09-monetization-and-go-to-market
**Requirements:** GTM-01 through GTM-12

## 1. x402 Machine Payment Protocol

### What It Is
x402 is Coinbase's open protocol for internet-native payments using the HTTP 402 status code. It enables AI agents to pay per-API-call in USDC on Base L2 without human intervention.

### How It Works (6-step flow)
1. Client requests a paid resource
2. Server responds with `402 Payment Required` + `PAYMENT-REQUIRED` header (base64 JSON with payment options)
3. Client constructs payment payload and signs it
4. Client retries request with `PAYMENT-SIGNATURE` header
5. Server validates via facilitator's `/verify` endpoint
6. Server settles payment via facilitator's `/settle` endpoint, returns resource + `PAYMENT-RESPONSE` header

### HTTP Headers
- `PAYMENT-REQUIRED` — Server -> Client: accepted payment schemes and networks (base64 encoded)
- `PAYMENT-SIGNATURE` — Client -> Server: signed payment payload (base64 encoded)
- `PAYMENT-RESPONSE` — Server -> Client: settlement confirmation (base64 encoded)

### Python FastAPI Integration
Package: `pip install "x402[fastapi]"` (v2.5.0, released 2026-03-20)
Also install: `"x402[evm]"` for Base/Ethereum support

```python
from x402 import x402ResourceServer, ResourceConfig
from x402.http import HTTPFacilitatorClient
from x402.mechanisms.evm.exact import ExactEvmServerScheme

facilitator = HTTPFacilitatorClient(url="https://x402.org/facilitator")
server = x402ResourceServer(facilitator)
server.register("eip155:*", ExactEvmServerScheme())
server.initialize()

config = ResourceConfig(
    scheme="exact",
    network="eip155:8453",  # Base Mainnet
    pay_to="0xYOUR_WALLET",
    price="$0.05",
)
requirements = server.build_payment_requirements(config)
```

### Network Identifiers (CAIP-2)
- Base Mainnet: `eip155:8453`
- Base Sepolia testnet: `eip155:84532`

### Facilitator
Use `https://x402.org/facilitator` for testnet. Production options: Coinbase CDP or PayAI facilitator.

### Lifecycle Hooks
```python
server.on_before_verify(lambda ctx: print(f"Verifying: {ctx.payload}"))
server.on_after_verify(lambda ctx: print(f"Valid: {ctx.result.is_valid}"))
server.on_verify_failure(lambda ctx: print(f"Error: {ctx.error}"))
```

### Per-Call Pricing (from requirements)
- render: $0.05
- generate: $0.10
- finance slides: $0.15
- batch: $0.08/deck

### Implementation Pattern for DeckForge
Create FastAPI middleware that:
1. Checks if request has `PAYMENT-SIGNATURE` header (x402 path)
2. If yes: verify payment via facilitator, settle, proceed to endpoint
3. If no: check for `X-API-Key` header (existing Unkey path)
4. If neither: return 402 with payment requirements OR 401 (missing API key)

This dual-auth pattern allows both agent (x402) and human (API key) access.

---

## 2. Unkey API Key Management

### What It Is
Managed API key infrastructure. Replaces custom auth middleware (our current SHA-256 hash lookup) with hosted key management, built-in rate limiting, and usage tracking.

### Python SDK
Package: `pip install unkey` (v3.0.1, released 2026-03-20)

```python
from unkey import Unkey

unkey = Unkey(root_key="unkey_ROOT_KEY")

# Create a key
result = unkey.keys.create_key(
    api_id="api_xxxx",
    name="My Key",
    prefix="dk_live",
    meta={"tier": "pro", "user_id": "usr_123"},
    ratelimit=[
        {"name": "requests", "limit": 60, "duration": 60000, "auto_apply": True}
    ]
)
print(result.key)  # dk_live_xxxxx

# Verify a key
result = unkey.keys.verify_key(key="dk_live_xxxxx")
# result.valid (bool), result.code (VALID/NOT_FOUND/RATE_LIMITED),
# result.meta, result.ratelimit, result.remaining
```

### Key Features
- **Key creation**: Prefix support (dk_live_, dk_test_), metadata, expiration, remaining uses
- **Key verification**: Single API call returns validity, rate limit status, metadata, remaining credits
- **Rate limiting**: Built-in, no Redis needed. Per-key limits with named limiters (e.g., "requests": 60/min)
- **Usage tracking**: Credits system with automatic refill. Keys can have remaining-use limits.
- **Key rotation**: Update key metadata, revoke old keys, create replacement keys
- **Never stores plaintext**: Keys hashed before storage (like our current approach)

### Rate Limiting
- Configured at key creation time with named limiters
- Auto-apply limits evaluate during every verification
- Manual limits specified at verification time for operation-specific costs
- Identity-level shared quotas across multiple keys

### Migration from Custom Auth
Replace `src/deckforge/api/middleware/auth.py` (SHA-256 hash lookup) with Unkey verify call.
Replace `src/deckforge/api/middleware/rate_limit.py` (Redis token bucket) with Unkey built-in rate limiting.

### Tier Mapping
- Starter: ratelimit 10/min, 50 credits remaining
- Pro: ratelimit 60/min, 500 credits remaining
- Enterprise: ratelimit 600/min, 10000 credits remaining

---

## 3. MCP Server for Agent Discovery

### What It Is
Model Context Protocol (MCP) server that exposes DeckForge functionality as tools that AI agents can discover and call.

### Python SDK
Package: `pip install "mcp[cli]"` (v1.26.0)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DeckForge", json_response=True)

@mcp.tool()
async def render(ir_json: str, theme: str = "corporate_navy") -> str:
    """Render a presentation from IR JSON. Returns download URL."""
    # Call DeckForge API internally
    ...

@mcp.tool()
async def generate(prompt: str, slide_count: int = 10) -> str:
    """Generate a presentation from natural language prompt."""
    ...

@mcp.tool()
def list_themes() -> list[dict]:
    """List all available presentation themes with color previews."""
    ...

@mcp.tool()
def list_slide_types() -> list[dict]:
    """List all 32 slide types with descriptions and categories."""
    ...
```

### Transport Options
- **stdio**: For local development and Claude Desktop integration
- **Streamable HTTP**: Recommended for production (both stateful and stateless modes)
- **SSE**: For streaming responses

### Tool Schema
Each tool auto-generates JSON Schema from Python type hints:
```json
{
  "name": "render",
  "description": "Render a presentation from IR JSON",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ir_json": {"type": "string"},
      "theme": {"type": "string", "default": "corporate_navy"}
    },
    "required": ["ir_json"]
  }
}
```

### x402 + MCP Integration
The x402 docs have a dedicated guide for MCP+x402. Pattern: MCP server wraps API calls with x402 payment handling. The `@x402/axios` wrapper auto-detects 402 responses and handles payment signing.

For DeckForge: The MCP server calls DeckForge API endpoints. If x402 is enabled, the MCP client's HTTP wrapper handles payment automatically. Agents pay per-tool-call.

---

## 4. Landing Page

### Architecture Decision
Build with Next.js static export for the landing page. Can be a separate `/landing` directory or a simple static HTML/Tailwind page served from a CDN.

### Recommended: Static HTML + Tailwind CSS
Given DeckForge is a Python API, a static landing page is simpler:
- Single `landing/index.html` with Tailwind CDN
- No build step, deploy to any static host (Vercel, Cloudflare Pages, GitHub Pages)
- Sections: Hero, Features Grid, Pricing Table, Live API Demo, Code Examples, CTA

### Key Sections
1. **Hero**: "Executive-ready slides, one API call away" + code snippet
2. **Feature Grid**: 6 cards (IR Schema, Layout Engine, Chart Engine, Finance Vertical, Google Slides, QA Pipeline)
3. **Pricing Table**: Starter/Pro/Enterprise + x402 per-call prices
4. **Live Demo**: curl command with copy button, or interactive form
5. **Code Examples**: TypeScript SDK, curl, Python requests
6. **CTA**: "Get Your API Key" -> sign up flow

---

## 5. npm SDK Publishing

### Current State
SDK is at `sdk/` directory, version 0.1.0, builds with tsup, dual ESM/CJS output.
67 tests passing, TypeScript strict mode.

### GitHub Actions Workflow
```yaml
name: Publish SDK
on:
  push:
    tags: ['sdk-v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, registry-url: 'https://registry.npmjs.org' }
      - run: cd sdk && npm ci && npm test && npm run build && npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Semantic Versioning
- Tag `sdk-v0.1.0` triggers publish of 0.1.0
- README with quick start, API reference via typedoc

---

## 6. GET /v1/pricing Endpoint

### Schema
```json
{
  "tiers": [
    {
      "name": "starter",
      "price_monthly_usd": 0,
      "credits_included": 50,
      "rate_limit_per_min": 10,
      "overage_rate_usd": 0.50
    },
    {
      "name": "pro",
      "price_monthly_usd": 79,
      "credits_included": 500,
      "rate_limit_per_min": 60,
      "overage_rate_usd": 0.30
    },
    {
      "name": "enterprise",
      "price_monthly_usd": null,
      "credits_included": "custom",
      "rate_limit_per_min": 600,
      "overage_rate_usd": "volume"
    }
  ],
  "x402_per_call": {
    "currency": "USDC",
    "network": "eip155:8453",
    "prices": {
      "render": "0.05",
      "generate": "0.10",
      "finance": "0.15",
      "batch_per_deck": "0.08"
    }
  }
}
```

Machine-readable. Agents call this to decide whether to pay per-call or get an API key.

---

## 7. Usage Analytics

### Data Sources
- Existing `usage_records` table (from Phase 8 billing)
- x402 payment events (new, from settlement callbacks)
- Unkey verification logs (via Unkey analytics API or local tracking)

### Dashboard Endpoints
- GET /v1/analytics/overview — total calls, revenue split (Stripe vs x402), active consumers
- GET /v1/analytics/endpoints — calls per endpoint (render, generate, preview, etc.)
- GET /v1/analytics/consumers — top consumers by usage
- GET /v1/analytics/revenue — daily/weekly/monthly revenue trends

### Implementation
Add `PaymentEvent` model to track x402 payments alongside existing `UsageRecord` for Stripe credits. Aggregate queries via SQLAlchemy for the dashboard.

---

## Technology Stack Summary

| Component | Library | Version | Install |
|-----------|---------|---------|---------|
| x402 payments | x402 | 2.5.0 | `pip install "x402[fastapi,evm]"` |
| API key mgmt | unkey | 3.0.1 | `pip install unkey` |
| MCP server | mcp | 1.26.0 | `pip install "mcp[cli]"` |
| Landing page | Tailwind CSS | 4.x | CDN link |
| SDK publish | GitHub Actions | - | `.github/workflows/publish-sdk.yml` |

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| x402 facilitator downtime | Fall back to API key auth; x402 is additive, not required |
| Unkey API latency | Cache verification results for 30s; fallback to local DB lookup |
| MCP protocol changes | Pin mcp SDK version; MCP is stable as of v1.26 |
| npm publish credentials | Use GitHub Actions secrets; never commit NPM_TOKEN |

## Architecture Pattern: Dual Auth

The key architectural insight for Phase 9 is **dual authentication**:
1. **Human path**: Unkey API key -> rate limit -> credit check -> serve
2. **Agent path**: x402 payment header -> verify -> settle -> serve
3. Both paths converge at the same endpoint handler

This is implemented as FastAPI middleware that checks headers in order:
- `PAYMENT-SIGNATURE` present? -> x402 flow
- `X-API-Key` present? -> Unkey flow
- Neither? -> Return 402 (with payment requirements) or 401

---

*Research conducted: 2026-03-26*
*Sources: x402.org, docs.x402.org, unkey.com, modelcontextprotocol.io, pypi.org*
