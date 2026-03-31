# DeckForge -- Render Deployment Guide

## Architecture (v0.1 MVP)

| Service | Render Type | Plan | Region |
|---------|-------------|------|--------|
| `deckforge-api` | Web Service (Docker) | Starter ($7/mo) | Frankfurt |
| `deckforge-db` | PostgreSQL | Free | Frankfurt |
| `deckforge-redis` | Redis | Free | Frankfurt |

v0.1 runs **sync rendering only** (decks under 10 slides). No background workers needed. The Dockerfile.render is a slim build without Chromium or LibreOffice -- just python-pptx, Plotly/Kaleido for charts, and fonts for text measurement.

## Deployment Steps

### 1. Push to GitHub

Ensure the repo is up to date:

```bash
git push origin master
```

### 2. Create Blueprint on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** at the top right
3. Select **Blueprint**
4. Connect to the **Whatsonyourmind/deckforge** repository
5. Render auto-detects `render.yaml` and shows the planned resources:
   - Web Service: `deckforge-api`
   - PostgreSQL: `deckforge-db`
   - Redis: `deckforge-redis`
6. Click **Apply**

### 3. Set Environment Variables

After the Blueprint is applied, go to the `deckforge-api` service and set these secrets (marked `sync: false` in render.yaml):

| Variable | Description | Required |
|----------|-------------|----------|
| `DECKFORGE_ANTHROPIC_API_KEY` | Anthropic API key for AI content generation | Yes |
| `DECKFORGE_STRIPE_SECRET_KEY` | Stripe secret key | For billing |
| `DECKFORGE_STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | For billing |
| `DECKFORGE_STRIPE_STARTER_PRICE_ID` | Stripe Starter plan price ID | For billing |
| `DECKFORGE_STRIPE_PRO_PRICE_ID` | Stripe Pro plan price ID | For billing |
| `DECKFORGE_UNKEY_ROOT_KEY` | Unkey root key for API key management | For prod auth |
| `DECKFORGE_UNKEY_API_ID` | Unkey API ID | For prod auth |
| `DECKFORGE_S3_ENDPOINT_URL` | S3-compatible storage endpoint (e.g., Cloudflare R2) | For file storage |
| `DECKFORGE_S3_ACCESS_KEY` | S3 access key | For file storage |
| `DECKFORGE_S3_SECRET_KEY` | S3 secret key | For file storage |

The following are auto-set by the Blueprint:
- `DECKFORGE_DATABASE_URL` -- from the managed PostgreSQL instance
- `DECKFORGE_REDIS_URL` -- from the managed Redis instance
- `DECKFORGE_ENVIRONMENT` -- set to `production`
- `DECKFORGE_LLM_DEFAULT_PROVIDER` -- set to `anthropic`
- `DECKFORGE_S3_BUCKET` -- set to `deckforge`

### 4. Run Database Migrations

After the first deploy completes, run Alembic migrations via the Render shell:

1. Go to the `deckforge-api` service in Render Dashboard
2. Click **Shell** tab
3. Run:
   ```bash
   alembic upgrade head
   ```

Alternatively, you can add a pre-deploy command in the Render dashboard:
- Settings -> Pre-Deploy Command: `alembic upgrade head`

### 5. Verify Deployment

Check the health endpoint:

```bash
curl https://deckforge-api.onrender.com/v1/health
```

Expected response:
```json
{"status": "ok"}
```

### 6. Configure Stripe Webhook (Optional)

If using Stripe billing, add a webhook endpoint in the Stripe Dashboard:
- URL: `https://deckforge-api.onrender.com/v1/billing/webhook`
- Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`

## URLs

| Resource | URL |
|----------|-----|
| API | https://deckforge-api.onrender.com |
| Health | https://deckforge-api.onrender.com/v1/health |
| Landing | https://landing-two-beta-63.vercel.app |
| SDK (npm) | https://www.npmjs.com/package/@lukastan/deckforge |
| GitHub | https://github.com/Whatsonyourmind/deckforge |

## Upgrading to v0.2 (Workers)

When ready to add async rendering for large decks (10+ slides):

1. Add a Background Worker service in render.yaml:
   ```yaml
   - type: worker
     name: deckforge-render-worker
     runtime: docker
     dockerfilePath: ./Dockerfile.render
     region: frankfurt
     plan: starter
     envVars:
       # Same DB + Redis vars as the web service
   ```

2. The worker command: `arq deckforge.workers.settings.RenderWorkerSettings`

3. For thumbnail generation, switch to the full `Dockerfile` (includes Chromium + LibreOffice).

## Troubleshooting

- **Build fails on psycopg**: The Dockerfile.render installs `libpq-dev` in both stages. If the builder stage fails, ensure `gcc` is present.
- **Health check fails**: Render expects the health check at `/v1/health`. Verify the port is using `$PORT` from env (Render injects this).
- **Database connection**: The `fromDatabase` reference in render.yaml auto-injects the internal connection string. No manual setup needed.
- **Cold starts**: Render Starter plan may spin down after 15min of inactivity. First request after sleep takes ~30s.
