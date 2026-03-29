---
phase: 11-production-launch
plan: 03
subsystem: ci-cd-docs
tags: [github-actions, ci-cd, stripe, fly-io, unkey, x402, npm, deployment, documentation]

requires:
  - phase: 11-production-launch
    plan: 01
    provides: README.md, .env.example, bootstrap-db.sh
  - phase: 11-production-launch
    plan: 02
    provides: Verification scripts (Docker, smoke test, demo validation)
provides:
  - GitHub Actions CI pipeline (pytest + vitest + typecheck on push/PR)
  - GitHub Actions deploy pipeline (Fly.io on push to main after CI)
  - Stripe product/price/webhook setup script
  - Complete deployment documentation for Fly.io, Unkey, x402, npm SDK
affects: [production-deployment, external-service-configuration]

tech-stack:
  added: []
  patterns: [reusable-workflow-call, stripe-client-api, flyctl-remote-deploy]

key-files:
  created:
    - .github/workflows/ci.yml
    - .github/workflows/deploy.yml
    - scripts/setup-stripe.py
    - docs/deployment.md
    - docs/unkey-setup.md
    - docs/x402-setup.md
    - docs/npm-publish.md
  modified:
    - README.md

key-decisions:
  - "CI installs .[preview,dev] extras since pyproject.toml has [dev] not [test] dependency group"
  - "ci.yml includes workflow_call trigger for reuse by deploy.yml"
  - "Stripe setup uses new StripeClient API per project decision [08-02]"
  - "Deployment docs cover R2 and Tigris as S3 storage options"

patterns-established:
  - "Reusable workflow pattern: ci.yml called by deploy.yml via workflow_call"
  - "Stripe setup script with --live / --skip-webhook flags and env var output"

requirements-completed: [LAUNCH-08, LAUNCH-09, LAUNCH-10, LAUNCH-11, LAUNCH-12]

duration: 4min
completed: 2026-03-29
---

# Phase 11 Plan 03: Deployment and CI/CD Summary

**GitHub Actions CI/CD (pytest+vitest on push, Fly.io deploy on main), Stripe 3-tier setup script, and complete deployment docs for Fly.io, Unkey, x402, and npm SDK publishing**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-29T21:28:17Z
- **Completed:** 2026-03-29T21:32:30Z
- **Tasks:** 2
- **Files created:** 7
- **Files modified:** 1

## Accomplishments

- GitHub Actions CI workflow with Python tests (pytest, Postgres + Redis service containers, mypy type check) and SDK tests (vitest, typecheck, build) running on push to main and PRs
- CI workflow includes `workflow_call` trigger enabling reuse by deploy workflow
- Deploy workflow triggers on main push, runs CI first via reusable workflow call, then deploys to Fly.io with flyctl
- scripts/setup-stripe.py creates 3 Stripe products (Starter $0, Pro $79, Enterprise custom), monthly prices, metered overage pricing ($0.30/credit), and webhook endpoint matching the 5 event types handled by stripe_webhooks.py
- docs/deployment.md (334 lines): Complete Fly.io guide covering Postgres, Redis, R2/Tigris storage, all environment secrets, deploy, migrations, scaling, custom domain, monitoring, Stripe setup, CI/CD setup, and troubleshooting
- docs/unkey-setup.md (111 lines): Workspace creation, API setup, root key permissions, local dev fallback to DB auth
- docs/x402-setup.md (161 lines): Wallet setup (MetaMask/Coinbase), Base L2 network, per-call pricing table, facilitator, testnet testing with Base Sepolia
- docs/npm-publish.md (161 lines): Automated tag-based publishing via existing workflow, manual fallback, version strategy, GitHub secret setup
- README.md updated with CI status badge linking to GitHub Actions

## Task Commits

Each task was committed atomically:

1. **Task 1: CI/CD pipelines and Stripe setup script** - `60b6228` (feat)
2. **Task 2: Deployment and service setup documentation** - `9f4c879` (feat)

## Files Created/Modified

- `.github/workflows/ci.yml` - CI pipeline: pytest (Postgres/Redis), mypy, vitest, typecheck, build
- `.github/workflows/deploy.yml` - Deploy pipeline: reuses CI, deploys to Fly.io with FLY_API_TOKEN
- `scripts/setup-stripe.py` - Stripe product/price/webhook configuration script with test/live modes
- `docs/deployment.md` - Complete Fly.io deployment guide (334 lines)
- `docs/unkey-setup.md` - Unkey workspace and API key management setup (111 lines)
- `docs/x402-setup.md` - x402 USDC wallet and payment setup (161 lines)
- `docs/npm-publish.md` - npm SDK publishing guide with automated and manual paths (161 lines)
- `README.md` - Added CI status badge

## Decisions Made

- CI workflow installs `.[preview,dev]` because pyproject.toml defines test dependencies under `[dev]` extra, not `[test]` as the plan template assumed
- ci.yml includes `workflow_call` trigger alongside push/pull_request so deploy.yml can reuse it as a called workflow
- Stripe setup uses new `stripe.StripeClient` API (not legacy `stripe.api_key` pattern) consistent with project decision [08-02]
- Deployment docs present Cloudflare R2 as recommended S3 option (no egress fees) with Fly Tigris as alternative

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed dependency group in CI workflow**
- **Found during:** Task 1
- **Issue:** Plan template used `pip install ".[preview,test]"` but pyproject.toml defines test dependencies under `[dev]` optional-dependency group, not `[test]`
- **Fix:** Changed to `pip install ".[preview,dev]"` to install both preview and development/test dependencies
- **Files modified:** .github/workflows/ci.yml
- **Committed in:** 60b6228

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential correction matching actual pyproject.toml structure. No scope creep.

## Issues Encountered

None.

## User Setup Required

Before CI/CD works in production:
- Add `FLY_API_TOKEN` as GitHub repository secret (for deploy workflow)
- Add `NPM_TOKEN` as GitHub repository secret (for SDK publish workflow, already documented)

## Project Completion

This is the FINAL plan (11-03) of the FINAL phase (11). With this plan complete:

- **31/31 plans executed** across 11 phases
- **All 104 v1 requirements** addressed
- **Full production deployment path** documented from git clone to live service
- **CI/CD pipeline** automated for testing and deployment
- **All external services** (Stripe, Unkey, x402, npm) documented with setup guides

DeckForge is ready for production launch.

## Self-Check: PASSED

All files verified present on disk. All commit hashes verified in git log.
