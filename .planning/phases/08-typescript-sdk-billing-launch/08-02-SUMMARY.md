---
phase: 08-typescript-sdk-billing-launch
plan: 02
subsystem: payments
tags: [stripe, billing, credits, metering, fastapi, sqlalchemy]

# Dependency graph
requires:
  - phase: 07-qa-pipeline-deck-operations
    provides: CostEstimator for credit cost estimation, render_pipeline integration
provides:
  - Tier definitions (Starter/Pro/Enterprise) with credit limits and overage rates
  - CreditManager with reserve/deduct/release lifecycle
  - UsageRecord and CreditReservation DB models
  - Stripe client for subscriptions, metering, checkout, and portal
  - Credit check middleware gating render/generate endpoints
  - Billing API with usage dashboard and Stripe webhook handler
affects: [08-typescript-sdk-billing-launch]

# Tech tracking
tech-stack:
  added: [stripe]
  patterns: [credit-reservation-lifecycle, billing-middleware, stripe-webhooks]

key-files:
  created:
    - src/deckforge/billing/__init__.py
    - src/deckforge/billing/tiers.py
    - src/deckforge/billing/credits.py
    - src/deckforge/billing/stripe_client.py
    - src/deckforge/billing/stripe_webhooks.py
    - src/deckforge/db/models/usage.py
    - src/deckforge/db/repositories/usage.py
    - src/deckforge/api/middleware/credits.py
    - src/deckforge/api/routes/billing.py
    - src/deckforge/api/schemas/billing_schemas.py
    - alembic/versions/004_billing_tables.py
    - tests/test_billing.py
  modified:
    - src/deckforge/db/models/__init__.py
    - src/deckforge/db/repositories/__init__.py
    - src/deckforge/api/app.py
    - src/deckforge/api/routes/render.py
    - src/deckforge/api/routes/generate.py
    - src/deckforge/config.py

key-decisions:
  - "UsageRecord __init__ with setdefault for credits_used/credits_reserved to ensure Python-level defaults (SA 2.0 mapped_column default is INSERT-only)"
  - "Enterprise tier allows overage (no InsufficientCreditsError), Starter/Pro block when credits exhausted"
  - "CreditCheck middleware reads raw request body for slide count estimation before CostEstimator"
  - "Stripe StripeClient uses new stripe.StripeClient API (not legacy module-level stripe.api_key)"

patterns-established:
  - "Credit reservation lifecycle: reserve before render -> deduct on success -> release on failure"
  - "CreditCheck as FastAPI Depends storing reservation on request.state for post-render accounting"
  - "Stripe webhook handler with event-type dispatch table pattern"

requirements-completed: [BILL-01, BILL-02, BILL-03, BILL-04, BILL-05, BILL-06]

# Metrics
duration: 6min
completed: 2026-03-29
---

# Phase 08 Plan 02: Billing System Summary

**Three-tier billing with Stripe metered credits, reserve/deduct/release lifecycle, and usage dashboard API**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T07:54:04Z
- **Completed:** 2026-03-29T08:00:38Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Three billing tiers (Starter free/50cr, Pro $79/500cr, Enterprise custom/10000cr) with overage rates
- Atomic credit reservation system preventing over-consumption on concurrent renders
- Stripe integration: subscriptions, metering, checkout sessions, billing portal, webhook handler
- Credit check middleware wired into /v1/render and /v1/generate (returns 402 when insufficient)
- Usage dashboard API returning current period and 12-month history

## Task Commits

Each task was committed atomically:

1. **Task 1: Tier definitions, credit management, and usage DB models** - `45eb2a8` (test: TDD RED) + `3deddff` (feat: TDD GREEN)
2. **Task 2: Stripe integration, credit middleware, billing API, and usage dashboard** - `dbf28fa` (feat)

**Plan metadata:** (pending)

_Note: Task 1 used TDD flow -- tests committed by previous attempt, implementation completed in this run._

## Files Created/Modified
- `src/deckforge/billing/__init__.py` - Billing module init
- `src/deckforge/billing/tiers.py` - Tier definitions (Starter/Pro/Enterprise) with Pydantic model
- `src/deckforge/billing/credits.py` - CreditManager with reserve/deduct/release and InsufficientCreditsError
- `src/deckforge/billing/stripe_client.py` - Stripe API wrapper for subscriptions, metering, checkout, portal
- `src/deckforge/billing/stripe_webhooks.py` - Webhook signature verification and event handler dispatch
- `src/deckforge/db/models/usage.py` - UsageRecord and CreditReservation SQLAlchemy models
- `src/deckforge/db/repositories/usage.py` - UsageRepository with atomic SELECT FOR UPDATE operations
- `src/deckforge/api/middleware/credits.py` - CreditCheck FastAPI dependency, CreditDeduct, CreditRelease
- `src/deckforge/api/routes/billing.py` - 5 billing routes (usage, history, checkout, portal, webhook)
- `src/deckforge/api/schemas/billing_schemas.py` - Billing response schemas
- `alembic/versions/004_billing_tables.py` - Migration for usage_records and credit_reservations tables
- `tests/test_billing.py` - 19 tests: tiers, credit lifecycle, usage model defaults
- `src/deckforge/db/models/__init__.py` - Added UsageRecord, CreditReservation imports
- `src/deckforge/db/repositories/__init__.py` - Added usage_repo singleton
- `src/deckforge/api/app.py` - Wired billing_router into app
- `src/deckforge/api/routes/render.py` - Added CreditCheck dependency to /v1/render
- `src/deckforge/api/routes/generate.py` - Added CreditCheck dependency to /v1/generate
- `src/deckforge/config.py` - Added Stripe env vars (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, etc.)

## Decisions Made
- UsageRecord uses `__init__` with `setdefault` pattern for Python-level defaults since SQLAlchemy 2.0 `mapped_column(default=)` only sets INSERT defaults, not Python init defaults
- Enterprise tier permits overage (credits can exceed limit, tracked for billing); Starter/Pro block with InsufficientCreditsError
- Stripe client uses new `stripe.StripeClient` instance API rather than legacy module-level `stripe.api_key` pattern
- CreditCheck middleware parses raw request body to estimate credit cost from slide count before processing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed UsageRecord default values not applied at Python level**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** `mapped_column(default=0)` only sets INSERT-time defaults in SA 2.0, so `UsageRecord()` constructed without session had `credits_used=None` instead of 0
- **Fix:** Added `__init__` method with `kwargs.setdefault("credits_used", 0)` pattern
- **Files modified:** `src/deckforge/db/models/usage.py`
- **Verification:** All 19 tests pass including `test_usage_record_default_credits`
- **Committed in:** `3deddff` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Bug fix necessary for test correctness. No scope creep.

## Issues Encountered
- Previous execution attempt partially completed (TDD RED committed, implementation files created but not committed). Identified existing state, verified tests, and continued from the GREEN phase.

## User Setup Required

External services require manual Stripe configuration:
- `DECKFORGE_STRIPE_SECRET_KEY` - Stripe Dashboard -> Developers -> API keys -> Secret key
- `DECKFORGE_STRIPE_WEBHOOK_SECRET` - Stripe Dashboard -> Developers -> Webhooks -> Signing secret
- `DECKFORGE_STRIPE_STARTER_PRICE_ID` - Stripe Dashboard -> Products -> DeckForge Starter -> Price ID
- `DECKFORGE_STRIPE_PRO_PRICE_ID` - Stripe Dashboard -> Products -> DeckForge Pro -> Price ID
- Create products: DeckForge Starter (free), DeckForge Pro ($79/mo) in Stripe Dashboard
- Create Billing Meter: deckforge_credit_usage (sum aggregation)
- Create webhook endpoint pointing to /v1/stripe/webhook

## Next Phase Readiness
- Billing system complete with all BILL-01 through BILL-06 requirements
- Credit check middleware is live on render and generate endpoints
- Stripe integration ready once API keys are configured
- Phase 08 billing plan complete

## Self-Check: PASSED

All 12 created files verified present. All 3 commit hashes (45eb2a8, 3deddff, dbf28fa) verified in git log. 19/19 tests passing.

---
*Phase: 08-typescript-sdk-billing-launch*
*Completed: 2026-03-29*
