# DeckForge — Fly.io Deployment Guide

The `fly.toml` is already configured. Follow these steps to deploy.

## Prerequisites

1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `flyctl auth login` (opens browser)

## Deploy

```bash
cd /path/to/deckforge

# Create the app (first time only)
fly apps create deckforge-api

# Set secrets
fly secrets set \
  DECKFORGE_DATABASE_URL="postgresql+asyncpg://user:pass@host/deckforge" \
  DECKFORGE_REDIS_URL="redis://host:6379" \
  DECKFORGE_S3_ENDPOINT="https://your-r2.r2.cloudflarestorage.com" \
  DECKFORGE_S3_ACCESS_KEY="your-key" \
  DECKFORGE_S3_SECRET_KEY="your-secret" \
  DECKFORGE_S3_BUCKET="deckforge-prod" \
  DECKFORGE_STRIPE_SECRET_KEY="rk_live_..." \
  DECKFORGE_STRIPE_WEBHOOK_SECRET="whsec_..." \
  DECKFORGE_UNKEY_ROOT_KEY="unkey_..." \
  DECKFORGE_UNKEY_API_ID="api_..." \
  DECKFORGE_LLM_DEFAULT_PROVIDER="anthropic" \
  ANTHROPIC_API_KEY="sk-ant-..." \
  DECKFORGE_SECRET_KEY="$(openssl rand -hex 32)"

# Deploy
fly deploy

# Run migrations
fly ssh console -C "alembic upgrade head"

# Verify
curl https://deckforge-api.fly.dev/v1/health
```

## Architecture on Fly.io

The `fly.toml` configures:
- **api** process: uvicorn with 2 workers on port 8000
- **worker** process: ARQ render worker
- Shared-CPU 2x with 1GB RAM
- Auto-stop/start machines
- Min 1 machine running
- Force HTTPS
- Health check at `/v1/health`

## Scaling

```bash
# Scale API machines
fly scale count api=2 worker=1

# Upgrade machine size
fly scale vm shared-cpu-2x --memory 2048
```

## Managed Services Needed

- **PostgreSQL**: Fly Postgres (`fly postgres create`) or Neon/Supabase
- **Redis**: Fly Redis (`fly redis create`) or Upstash
- **Object Storage**: Cloudflare R2 (S3-compatible, free egress)
