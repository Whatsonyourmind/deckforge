# Unkey API Key Management Setup

Guide for configuring Unkey as DeckForge's production API key management system.

## What is Unkey?

[Unkey](https://unkey.com) is a cloud-hosted API key management service that handles key creation, verification, rotation, revocation, and usage metering. In production, DeckForge uses Unkey instead of the built-in database-based SHA-256 key authentication.

**Why Unkey over DB-based auth?**
- Sub-millisecond key verification (edge-cached globally)
- Built-in rate limiting and usage tracking
- Key rotation and revocation without DB migrations
- Dashboard for managing keys across environments

## 1. Create a Workspace

1. Sign up at [unkey.com](https://unkey.com)
2. Create a new workspace (e.g., "DeckForge Production")
3. Note your workspace ID from the Settings page

## 2. Create an API

1. In the Unkey dashboard, go to **APIs** > **Create API**
2. Name it `deckforge`
3. Copy the **API ID** (format: `api_...`)

This API represents all DeckForge API keys. Each user's key is an individual key within this API.

## 3. Create a Root Key

1. Go to **Settings** > **Root Keys** > **Create Root Key**
2. Grant these permissions:
   - `api.*.create_key` -- create API keys for new users
   - `api.*.verify_key` -- verify API keys on every request
   - `api.*.update_key` -- update key metadata (tier changes, etc.)
   - `api.*.delete_key` -- revoke API keys
3. Copy the root key (format: `unkey_...`)

**Important:** The root key is shown only once. Store it securely.

## 4. Configure DeckForge

### Production (Fly.io)

```bash
fly secrets set \
  DECKFORGE_UNKEY_ROOT_KEY="unkey_..." \
  DECKFORGE_UNKEY_API_ID="api_..." \
  --app deckforge-api
```

### Local Development (.env)

```bash
# Add to your .env file (optional -- local dev works without Unkey)
DECKFORGE_UNKEY_ROOT_KEY=unkey_...
DECKFORGE_UNKEY_API_ID=api_...
```

## 5. Local Development Fallback

Unkey is **optional** for local development. When `DECKFORGE_UNKEY_ROOT_KEY` is not set, DeckForge automatically falls back to database-based SHA-256 key authentication. This is by design (decision [09-03]).

The fallback behavior:
- `POST /v1/onboard/signup` creates keys in the local PostgreSQL database
- Key verification hashes the provided key with SHA-256 and looks it up in the `api_keys` table
- Rate limiting uses the Redis token bucket (same as production)

This means you can develop and test locally without an Unkey account.

## 6. Key Creation Flow

When Unkey is configured:

1. User calls `POST /v1/onboard/signup` with email and name
2. DeckForge creates a User record in PostgreSQL
3. DeckForge calls Unkey API to create a new key with metadata:
   - `userId`: DeckForge user ID
   - `tier`: "starter" (default)
   - `name`: User-provided key name
4. The raw API key (format: `dk_live_...` or `dk_test_...`) is returned once
5. On subsequent API calls, the key is verified against Unkey (not the DB)

## 7. Key Management

### Via Unkey Dashboard

- **View all keys:** APIs > deckforge > Keys
- **Revoke a key:** Click key > Delete
- **View usage:** Click key > Analytics
- **Rotate a key:** Delete the old key and create a new one via the API

### Via API

DeckForge exposes key management through the signup and billing endpoints. Direct Unkey API calls are also supported for advanced management:

```bash
# List keys (via Unkey API)
curl -H "Authorization: Bearer unkey_..." \
  "https://api.unkey.dev/v1/apis/api_.../keys"
```

## 8. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DECKFORGE_UNKEY_ROOT_KEY` | No | `None` | Unkey root key for key management |
| `DECKFORGE_UNKEY_API_ID` | No | `None` | Unkey API ID for the deckforge API |

Both must be set together. If either is missing, DeckForge falls back to DB-based auth.
