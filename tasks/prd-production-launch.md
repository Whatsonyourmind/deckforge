# PRD: DeckForge Production Launch

## Introduction

DeckForge's codebase is complete (10 phases, 28 plans, 137 commits, 434 files, 800+ tests) but has never been run as a live service. This PRD covers every gap between "code in a repo" and "live product accepting payments from humans and agents." The target: anyone can clone, configure, deploy, and start earning within 30 minutes.

## Goals

- Anyone can go from `git clone` to running API in under 10 minutes locally
- Production deployment on Fly.io serves real traffic with TLS
- Stripe accepts real payments (subscriptions + metered usage)
- npm SDK is published and installable
- x402 wallet receives USDC on Base
- First API call produces a real .pptx file that opens in PowerPoint
- Health check, auth, rate limiting, and billing all work end-to-end

## User Stories

### US-001: Production README
**Description:** As a developer, I want a root README.md that explains what DeckForge is, how to run it locally, and how to deploy it so I can get started in minutes.

**Acceptance Criteria:**
- [ ] README.md at repo root with: tagline, feature list, quick start (5 steps), API examples (curl), SDK example (TypeScript), architecture diagram (ASCII), environment variables table, deployment guide, pricing table, license
- [ ] Quick start works: clone, cp .env.example .env, docker compose up, curl health, curl render
- [ ] Links to sdk/README.md, landing page, and API docs
- [ ] Badges: Python version, license, tests passing, npm version

### US-002: Complete .env.example
**Description:** As a developer, I want .env.example to document every environment variable so I can configure the system without reading source code.

**Acceptance Criteria:**
- [ ] Every setting from config.py has a corresponding line in .env.example
- [ ] Each variable has a comment explaining what it does and example values
- [ ] Grouped by section: Core, Database, Redis, S3/Storage, Stripe, Unkey, x402, Google OAuth, LLM defaults
- [ ] Sensible defaults for local development (localhost URLs, test keys)
- [ ] `cp .env.example .env` produces a working local config (no edits needed for basic render)

### US-003: Docker Compose Smoke Test
**Description:** As a developer, I want to verify that `docker compose up` brings up all services and the API responds.

**Acceptance Criteria:**
- [ ] `docker compose up -d` starts all 6 services (api, worker-content, worker-render, redis, postgres, minio) without errors
- [ ] `docker compose ps` shows all services healthy
- [ ] `curl http://localhost:8000/v1/health` returns 200 with `{"status": "healthy"}`
- [ ] Alembic migrations run automatically on API startup (or documented as manual step)
- [ ] MinIO bucket created automatically

### US-004: End-to-End Render Test
**Description:** As a developer, I want to verify the full render pipeline works by generating an actual .pptx from an API call.

**Acceptance Criteria:**
- [ ] Script `scripts/smoke-test.sh` that: creates a test API key in DB, sends a render request with a 3-slide IR, saves the .pptx, verifies it's valid (file size > 5KB, starts with PK zip header)
- [ ] The .pptx opens without errors in PowerPoint/LibreOffice
- [ ] Script exits 0 on success, non-zero on failure
- [ ] Includes a generate test (NL prompt, if LLM key configured) with fallback skip

### US-005: Database Bootstrap Script
**Description:** As a developer, I want a script that initializes the database with required tables and seed data.

**Acceptance Criteria:**
- [ ] `scripts/bootstrap-db.sh` runs Alembic migrations and seeds: default admin user, test API key (dk_test_...), Starter/Pro/Enterprise subscription plans
- [ ] Idempotent (safe to run multiple times)
- [ ] Outputs the test API key for immediate use
- [ ] Works with both SQLite (dev) and PostgreSQL (production)

### US-006: npm SDK Publish
**Description:** As a developer, I want @deckforge/sdk installable from npm.

**Acceptance Criteria:**
- [ ] `npm install @deckforge/sdk` works
- [ ] Package includes: dist/index.js, dist/index.cjs, dist/index.d.ts
- [ ] README visible on npmjs.com with quick start and examples
- [ ] Version 0.1.0 matches GitHub release

### US-007: Fly.io Production Deployment
**Description:** As an operator, I want DeckForge deployed on Fly.io serving real traffic.

**Acceptance Criteria:**
- [ ] `fly deploy` succeeds from the repo root
- [ ] API accessible at https://deckforge.fly.dev (or custom domain)
- [ ] Health endpoint returns 200
- [ ] Render endpoint returns .pptx with valid API key
- [ ] PostgreSQL provisioned via Fly Postgres
- [ ] Redis provisioned via Upstash or Fly Redis
- [ ] S3 storage configured (Cloudflare R2 or Fly Tigris)
- [ ] Environment variables set via `fly secrets`

### US-008: Stripe Product Configuration
**Description:** As an operator, I want Stripe configured with the correct products, prices, and webhook.

**Acceptance Criteria:**
- [ ] `scripts/setup-stripe.py` creates: 3 products (Starter, Pro, Enterprise), monthly prices ($0, $79, custom), metered usage component
- [ ] Stripe webhook endpoint registered pointing to /v1/billing/webhook
- [ ] Webhook secret stored in fly secrets
- [ ] Test mode works with Stripe test keys
- [ ] Script outputs the price IDs to paste into .env

### US-009: Unkey Workspace Setup
**Description:** As an operator, I want Unkey configured for API key management.

**Acceptance Criteria:**
- [ ] Documentation for creating Unkey workspace and API
- [ ] UNKEY_ROOT_KEY and UNKEY_API_ID documented in .env.example
- [ ] Fallback to DB-based auth when Unkey is not configured (for local dev)
- [ ] Key creation via /v1/onboard/signup works with Unkey

### US-010: x402 Wallet Configuration
**Description:** As an operator, I want x402 USDC payments configured with a real wallet.

**Acceptance Criteria:**
- [ ] Documentation for setting up a USDC receiving wallet on Base
- [ ] RECEIVING_WALLET_ADDRESS in .env.example with placeholder
- [ ] x402 facilitator URL documented
- [ ] Test with Base testnet USDC documented

### US-011: CLAUDE.md Project Instructions
**Description:** As a developer using Claude Code, I want project-specific instructions that guide AI assistants.

**Acceptance Criteria:**
- [ ] CLAUDE.md at repo root with: project overview, tech stack, key commands (test, lint, build, deploy), architecture summary, coding conventions, important patterns (IR schema, renderer registry, layout patterns)
- [ ] Keeps Claude Code productive without reading the full codebase

### US-012: CI/CD Pipeline
**Description:** As a developer, I want automated tests and deployment on every push.

**Acceptance Criteria:**
- [ ] `.github/workflows/ci.yml` runs: Python tests (pytest), TypeScript SDK tests (vitest), type checking
- [ ] Triggered on push to main and PRs
- [ ] `.github/workflows/deploy.yml` deploys to Fly.io on push to main (after CI passes)
- [ ] Status badge in README

## Functional Requirements

- FR-1: Root README.md with full documentation (quick start, API reference, deployment, pricing)
- FR-2: .env.example with every environment variable documented and grouped
- FR-3: scripts/bootstrap-db.sh initializes database with migrations and seed data
- FR-4: scripts/smoke-test.sh verifies full render pipeline end-to-end
- FR-5: scripts/setup-stripe.py configures Stripe products, prices, and webhooks
- FR-6: Docker Compose brings up all services with one command
- FR-7: Fly.io deployment configuration (fly.toml, Procfile) verified working
- FR-8: GitHub Actions CI pipeline (test + deploy)
- FR-9: npm SDK published as @deckforge/sdk@0.1.0
- FR-10: CLAUDE.md with project instructions for AI assistants
- FR-11: All 5 demo deck IRs in demos/ render to valid .pptx files
- FR-12: Onboarding flow: signup → API key → first render in under 5 minutes

## Non-Goals

- No new features or API endpoints (codebase is complete)
- No UI/dashboard (API-only product)
- No custom domain setup (use fly.dev subdomain for now)
- No load testing or performance optimization (premature at 0 users)
- No monitoring/alerting setup (add after first paying customer)

## Technical Considerations

- Docker Compose already exists but needs verification with current codebase
- Alembic has 5 migrations that need to run in order
- Fly.io deployment uses multi-stage Dockerfile already in repo
- Stripe test mode for development, live mode for production
- SQLite for local dev (zero config), PostgreSQL for production
- MinIO for local S3, Cloudflare R2 for production

## Success Metrics

- Clone-to-first-render time < 10 minutes
- Deploy-to-live time < 30 minutes
- All demo decks render to valid .pptx
- Health check returns 200 on production
- npm install @deckforge/sdk succeeds
- Stripe test payment flows through

## Open Questions

- None. Ship it.
