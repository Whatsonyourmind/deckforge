---
phase: 09-monetization-and-go-to-market
plan: 01
subsystem: auth, payments, api
tags: [unkey, x402, usdc, base-l2, api-key, rate-limiting, pricing]

# Dependency graph
requires:
  - phase: 08-typescript-sdk-billing-launch
    provides: Stripe billing, credit middleware, API key model, FastAPI app
provides:
  - Unkey-based API key verification replacing SHA-256 DB auth
  - x402 payment middleware for USDC per-call payments on Base L2
  - Dual auth dependency (PAYMENT-SIGNATURE or X-API-Key)
  - Per-call pricing configuration (x402_config)
  - GET /v1/pricing public endpoint with tier + x402 pricing
  - AuthContext dataclass replacing ApiKey model in auth chain
affects: [09-02-mcp-server, 09-03-landing-page, all-protected-routes]

# Tech tracking
tech-stack:
  added: [unkey-py, x402, httpx (for Unkey API)]
  patterns: [dual-auth-middleware, auth-context-dataclass, facilitator-verify-settle]

key-files:
  created:
    - src/deckforge/api/middleware/x402.py
    - src/deckforge/billing/x402_config.py
    - src/deckforge/api/routes/pricing.py
    - src/deckforge/api/schemas/pricing_schemas.py
    - tests/test_auth_unkey.py
    - tests/test_x402.py
  modified:
    - src/deckforge/api/middleware/auth.py
    - src/deckforge/api/middleware/rate_limit.py
    - src/deckforge/config.py
    - src/deckforge/api/app.py
    - pyproject.toml

key-decisions:
  - "AuthContext dataclass with .id property for backwards compatibility with ApiKey model references"
  - "httpx for Unkey API calls (already in dependencies, avoids adding unkey SDK complexity)"
  - "Legacy Redis token bucket preserved for DB-auth fallback mode in development"
  - "x402 payments skip rate limiting (per-call payment is the throttle)"

patterns-established:
  - "Dual auth pattern: PAYMENT-SIGNATURE -> x402, X-API-Key -> Unkey/DB"
  - "AuthContext as unified auth result across all auth sources"
  - "x402_config route-to-price mapping for per-call pricing"

requirements-completed: [GTM-01, GTM-02, GTM-03, GTM-05, GTM-07]

# Metrics
duration: 7min
completed: 2026-03-29
---

# Phase 9 Plan 01: x402 + Unkey Dual Auth Summary

**Dual authentication with Unkey API keys and x402 USDC per-call payments on Base L2, plus GET /v1/pricing for agent discovery**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-29T18:10:55Z
- **Completed:** 2026-03-29T18:18:01Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Replaced SHA-256 custom auth with Unkey verification (DB fallback for development)
- Built x402 payment middleware for AI agent per-call USDC payments via facilitator
- Created GET /v1/pricing returning machine-readable tiers + x402 prices
- Rate limiting now flows through Unkey verify response (no Redis Lua for Unkey mode)
- 26 tests passing across auth and x402 test suites

## Task Commits

Each task was committed atomically:

1. **Task 1: Unkey auth + x402 payment middleware + pricing config** - `39fdc0d` (feat)
2. **Task 2: GET /v1/pricing endpoint + wire dual auth into app** - `baa9420` (feat)

## Files Created/Modified
- `src/deckforge/api/middleware/auth.py` - Unkey verification with DB fallback, AuthContext dataclass
- `src/deckforge/api/middleware/rate_limit.py` - Unkey rate_limited flag check, legacy Redis fallback
- `src/deckforge/api/middleware/x402.py` - x402 payment verification/settlement via facilitator
- `src/deckforge/billing/x402_config.py` - Route-to-price mapping for x402 per-call payments
- `src/deckforge/api/routes/pricing.py` - GET /v1/pricing public endpoint
- `src/deckforge/api/schemas/pricing_schemas.py` - PricingTier, X402PerCallPricing, PricingResponse models
- `src/deckforge/config.py` - Added UNKEY_* and X402_* settings
- `src/deckforge/api/app.py` - Wired pricing_router
- `pyproject.toml` - Added unkey-py and x402 dependencies
- `tests/test_auth_unkey.py` - 12 tests for Unkey auth and DB fallback
- `tests/test_x402.py` - 14 tests for x402 pricing and dual auth

## Decisions Made
- **AuthContext with .id property:** Added backwards-compatible `id` property on AuthContext that maps to `key_id`, since 20+ existing route references use `api_key.id` from the old ApiKey model
- **httpx for Unkey calls:** Used httpx directly for Unkey API verification rather than the unkey SDK, keeping the dependency lightweight and avoiding SDK version coupling
- **Legacy rate limiting preserved:** Redis token bucket kept for DB-auth mode so local development without Unkey still has rate limiting
- **x402 skips rate limiting:** Per-call payments are self-throttling (agents pay per request), so x402 auth source is exempt from rate limits

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added .id property to AuthContext for backwards compatibility**
- **Found during:** Task 1 (auth.py rewrite)
- **Issue:** 20+ existing routes reference `api_key.id` (UUID from ApiKey model); AuthContext uses `key_id` (string). Removing `.id` would break every protected route.
- **Fix:** Added `@property` on frozen dataclass that returns `self.key_id`
- **Files modified:** src/deckforge/api/middleware/auth.py
- **Verification:** All downstream routes still type-check; tests pass
- **Committed in:** 39fdc0d (Task 1 commit)

**2. [Rule 3 - Blocking] Moved httpx import to module level**
- **Found during:** Task 1 (test execution)
- **Issue:** Local import of httpx inside `_verify_via_unkey` prevented mock patching in tests
- **Fix:** Moved `import httpx` to module-level imports
- **Files modified:** src/deckforge/api/middleware/auth.py
- **Verification:** All 12 auth tests pass
- **Committed in:** 39fdc0d (Task 1 commit)

**3. [Rule 3 - Blocking] Moved get_db import to module level in x402.py**
- **Found during:** Task 1 (test execution)
- **Issue:** Local import of `get_db` inside `x402_or_apikey_auth` prevented test patching
- **Fix:** Moved import to module level
- **Files modified:** src/deckforge/api/middleware/x402.py
- **Verification:** All 14 x402 tests pass
- **Committed in:** 39fdc0d (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All fixes necessary for correctness and testability. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required

External services require manual configuration before production use:

**Unkey (API key management):**
1. Create an API named "DeckForge" in Unkey Dashboard (APIs -> Create)
2. Set `DECKFORGE_UNKEY_ROOT_KEY` from Workspace Settings -> Root Keys -> Create
3. Set `DECKFORGE_UNKEY_API_ID` from APIs -> DeckForge -> Copy API ID

**x402 Wallet (USDC payments):**
1. Designate an EVM wallet for receiving USDC on Base mainnet
2. Set `DECKFORGE_X402_WALLET_ADDRESS` to your wallet address
3. Set `DECKFORGE_X402_ENABLED=true` to activate x402 payments

**Verification:**
```bash
# Test Unkey auth (with key created in Unkey dashboard)
curl -H "X-API-Key: dk_live_yourkey" http://localhost:8000/v1/health

# Test pricing endpoint (no auth needed)
curl http://localhost:8000/v1/pricing
```

## Next Phase Readiness
- Dual auth infrastructure ready for MCP server (09-02) to use
- Pricing endpoint available for landing page (09-03) to link to
- x402 middleware ready for production once wallet address configured

---
*Phase: 09-monetization-and-go-to-market*
*Completed: 2026-03-29*
