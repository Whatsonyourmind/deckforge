# DeckForge Deployment Guide

Complete guide for deploying DeckForge to production on Fly.io.

## Prerequisites

- [Fly.io account](https://fly.io/app/sign-up) (free tier available)
- [flyctl CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- GitHub repository cloned locally
- Domain name (optional, `.fly.dev` subdomain provided free)

## 1. Initial Setup

### Launch the Fly App

```bash
# Login to Fly.io
fly auth login

# Launch the app (do NOT deploy yet -- we need to set secrets first)
fly launch --name deckforge-api --region iad --no-deploy
```

When prompted, accept the existing `fly.toml` configuration. The app uses:
- **Region:** `iad` (US East / Virginia)
- **VM:** shared-cpu-2x, 1 GB RAM
- **Processes:** `api` (uvicorn, 2 workers) + `worker` (ARQ task queue)

### Provision PostgreSQL

```bash
# Create a Postgres cluster
fly postgres create --name deckforge-db --region iad

# Attach it to the app (auto-sets DATABASE_URL secret)
fly postgres attach deckforge-db --app deckforge-api
```

The `fly postgres attach` command automatically sets `DATABASE_URL` as a Fly secret. DeckForge reads `DECKFORGE_DATABASE_URL`, so you may need to alias it:

```bash
# Get the auto-set DATABASE_URL value
fly secrets list --app deckforge-api

# Set with the DECKFORGE_ prefix
fly secrets set DECKFORGE_DATABASE_URL="postgres://..." --app deckforge-api
```

### Provision Redis

**Option A: Fly Redis (Upstash)**

```bash
fly redis create --name deckforge-redis --region iad
# Copy the Redis URL from the output
fly secrets set DECKFORGE_REDIS_URL="redis://..." --app deckforge-api
```

**Option B: External Upstash**

1. Sign up at [upstash.com](https://upstash.com)
2. Create a Redis database in the `us-east-1` region
3. Copy the Redis URL (TLS endpoint recommended)

```bash
fly secrets set DECKFORGE_REDIS_URL="rediss://default:PASSWORD@HOST:PORT" --app deckforge-api
```

### Configure S3-Compatible Storage

DeckForge stores generated presentations in S3-compatible storage. Choose one:

**Option A: Cloudflare R2 (recommended, no egress fees)**

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com) > R2
2. Create a bucket named `deckforge`
3. Go to **Manage R2 API Tokens** > Create API Token
4. Select **Object Read & Write** permissions for the `deckforge` bucket
5. Copy the Access Key ID, Secret Access Key, and S3 endpoint URL

```bash
fly secrets set \
  DECKFORGE_S3_ENDPOINT_URL="https://ACCOUNT_ID.r2.cloudflarestorage.com" \
  DECKFORGE_S3_ACCESS_KEY="your-r2-access-key" \
  DECKFORGE_S3_SECRET_KEY="your-r2-secret-key" \
  DECKFORGE_S3_BUCKET="deckforge" \
  --app deckforge-api
```

**Option B: Fly Tigris**

```bash
fly storage create --name deckforge-storage --app deckforge-api
# Tigris auto-configures S3 credentials as Fly secrets
```

## 2. Environment Secrets

Set all required production secrets. Some are auto-set by provisioning commands above.

```bash
fly secrets set \
  DECKFORGE_ENVIRONMENT=production \
  DECKFORGE_DEBUG=false \
  --app deckforge-api
```

### Required Secrets

| Secret | Source | Notes |
|--------|--------|-------|
| `DECKFORGE_DATABASE_URL` | `fly postgres attach` | Auto-set, may need DECKFORGE_ prefix |
| `DECKFORGE_REDIS_URL` | `fly redis create` | Copy from output |
| `DECKFORGE_S3_ENDPOINT_URL` | R2 / Tigris | S3-compatible endpoint |
| `DECKFORGE_S3_ACCESS_KEY` | R2 / Tigris | Access key |
| `DECKFORGE_S3_SECRET_KEY` | R2 / Tigris | Secret key |
| `DECKFORGE_S3_BUCKET` | Manual | Default: `deckforge` |
| `DECKFORGE_ENVIRONMENT` | Manual | Set to `production` |
| `DECKFORGE_DEBUG` | Manual | Set to `false` |

### LLM Provider (at least one required for /v1/generate)

```bash
# Pick one or more:
fly secrets set DECKFORGE_ANTHROPIC_API_KEY="sk-ant-..." --app deckforge-api
fly secrets set DECKFORGE_OPENAI_API_KEY="sk-..." --app deckforge-api
fly secrets set DECKFORGE_GEMINI_API_KEY="AI..." --app deckforge-api
```

The `/v1/render` endpoint works without any LLM key. Only `/v1/generate` (natural language to slides) requires one.

### Stripe Billing (optional, for paid tiers)

Run the setup script first (see [Stripe setup](#stripe-setup) below), then:

```bash
fly secrets set \
  DECKFORGE_STRIPE_SECRET_KEY="sk_live_..." \
  DECKFORGE_STRIPE_WEBHOOK_SECRET="whsec_..." \
  DECKFORGE_STRIPE_STARTER_PRICE_ID="price_..." \
  DECKFORGE_STRIPE_PRO_PRICE_ID="price_..." \
  --app deckforge-api
```

### Unkey API Keys (optional, for production auth)

See [docs/unkey-setup.md](unkey-setup.md) for workspace creation.

```bash
fly secrets set \
  DECKFORGE_UNKEY_ROOT_KEY="unkey_..." \
  DECKFORGE_UNKEY_API_ID="api_..." \
  --app deckforge-api
```

### x402 Machine Payments (optional, for agent billing)

See [docs/x402-setup.md](x402-setup.md) for wallet setup.

```bash
fly secrets set \
  DECKFORGE_X402_ENABLED=true \
  DECKFORGE_X402_WALLET_ADDRESS="0x..." \
  --app deckforge-api
```

## 3. Deploy

```bash
fly deploy
```

The deploy uses the multi-stage `Dockerfile`:
- **Stage 1 (builder):** Installs Python packages with gcc/libpq-dev
- **Stage 2 (runtime):** Slim image with Chromium (chart rendering), LibreOffice (thumbnails), fonts, poppler

First deploy takes 3-5 minutes (Docker image build). Subsequent deploys are faster with layer caching.

## 4. Database Migrations

After the first deploy, run Alembic migrations:

```bash
fly ssh console -C "alembic upgrade head" --app deckforge-api
```

For subsequent deploys, run migrations before or after deploy:

```bash
# Run migrations on already-deployed instance
fly ssh console -C "alembic upgrade head" --app deckforge-api
```

## 5. Verify

```bash
# Health check
curl https://deckforge-api.fly.dev/v1/health
# Expected: {"status":"healthy"}

# Check available themes (no auth required)
curl https://deckforge-api.fly.dev/v1/themes

# Check pricing info
curl https://deckforge-api.fly.dev/v1/pricing
```

## 6. Scaling

DeckForge uses two process types defined in `fly.toml`:

- **api:** FastAPI + uvicorn (handles HTTP requests)
- **worker:** ARQ task queue (handles async generation and rendering)

```bash
# Scale API to 2 instances, worker to 1
fly scale count api=2 worker=1 --app deckforge-api

# Check current scale
fly scale show --app deckforge-api

# Increase VM memory if needed (for large decks)
fly scale vm shared-cpu-2x --memory 2048 --app deckforge-api
```

## 7. Custom Domain (Optional)

```bash
# Add a custom domain
fly certs create deckforge.yourdomain.com --app deckforge-api

# Follow DNS instructions from the output (CNAME to deckforge-api.fly.dev)
fly certs show deckforge.yourdomain.com --app deckforge-api
```

## 8. Monitoring

```bash
# Live logs
fly logs --app deckforge-api

# Application status and VM info
fly status --app deckforge-api

# Open Fly dashboard in browser
fly dashboard --app deckforge-api

# SSH into a running instance for debugging
fly ssh console --app deckforge-api
```

## 9. Stripe Setup

Use the setup script to create Stripe products, prices, and webhook:

```bash
# Install stripe CLI package
pip install stripe

# Set your Stripe test key
export STRIPE_SECRET_KEY=sk_test_...

# Run setup (test mode by default)
python scripts/setup-stripe.py

# Or specify a custom webhook URL
python scripts/setup-stripe.py --webhook-url https://deckforge-api.fly.dev/v1/billing/webhook

# For live mode (production)
export STRIPE_SECRET_KEY=sk_live_...
python scripts/setup-stripe.py --live
```

The script creates:
- **Starter** product ($0/month, 50 credits)
- **Pro** product ($79/month, 500 credits)
- **Enterprise** product (custom pricing, 10,000 credits)
- **Overage** metered price ($0.30/credit)
- **Webhook** endpoint for subscription and payment events

Copy the output price IDs and webhook secret into Fly secrets.

## 10. CI/CD Setup

### GitHub Actions Secrets

The repository includes CI/CD workflows in `.github/workflows/`. Add these GitHub repository secrets:

| Secret | Purpose |
|--------|---------|
| `FLY_API_TOKEN` | Fly.io deploy token (`fly tokens create deploy`) |

### How It Works

1. **On push to main or PR:** `.github/workflows/ci.yml` runs Python tests (pytest with Postgres + Redis) and SDK tests (vitest + typecheck + build)
2. **On push to main (after CI passes):** `.github/workflows/deploy.yml` deploys to Fly.io
3. **On `sdk-v*` tag:** `.github/workflows/publish-sdk.yml` publishes the SDK to npm

## Troubleshooting

### Common Issues

**Port binding error:**
DeckForge binds to port 8000 by default. The `fly.toml` `internal_port` must match. Verify with `fly ssh console -C "env | grep PORT"`.

**Out of memory:**
Large decks with many charts consume memory for Plotly/Kaleido rendering. Scale up:
```bash
fly scale vm shared-cpu-2x --memory 2048 --app deckforge-api
```

**Cold start timeout:**
First request after idle may take 5-10 seconds (machine start + Python import). Set `min_machines_running = 1` in `fly.toml` (already configured) to keep one machine warm.

**Database connection refused:**
Verify Postgres is attached and URL is correct:
```bash
fly secrets list --app deckforge-api | grep DATABASE
fly postgres connect --app deckforge-db
```

**Redis connection error:**
Verify Redis URL includes the correct protocol (`redis://` or `rediss://` for TLS):
```bash
fly secrets list --app deckforge-api | grep REDIS
```

**Alembic migration error:**
If migrations fail, check the database state:
```bash
fly ssh console -C "alembic current" --app deckforge-api
fly ssh console -C "alembic history" --app deckforge-api
```
