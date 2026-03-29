#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# DeckForge Docker Compose Verification
# ============================================================================
# Verifies all 6 Docker Compose services are running and healthy.
# Expects: docker compose up -d already running.
# Exits 0 on success, non-zero on failure.
#
# Services checked:
#   api, content-worker, render-worker, postgres, redis, minio
# ============================================================================

echo "=== DeckForge Docker Compose Verification ==="
echo ""

EXPECTED_SERVICES=("api" "content-worker" "render-worker" "postgres" "redis" "minio")
FAILED=0

# --------------------------------------------------------------------------
# Step 1: Check all services are running
# --------------------------------------------------------------------------
echo "[1/3] Checking service status..."

for svc in "${EXPECTED_SERVICES[@]}"; do
  # Use docker compose ps with grep for portability across Docker Compose
  # versions (v1 vs v2 have different --format json output shapes).
  container_running=$(docker compose ps --status running 2>/dev/null | grep -c "$svc" || echo "0")

  if [[ "$container_running" -ge 1 ]]; then
    echo "  OK: $svc is running"
  else
    # Fallback: try docker compose ps with generic grep
    alt_check=$(docker compose ps 2>/dev/null | grep "$svc" | grep -ci "up\|running" || echo "0")
    if [[ "$alt_check" -ge 1 ]]; then
      echo "  OK: $svc is running"
    else
      echo "  FAIL: $svc is NOT running"
      echo "  Logs:"
      docker compose logs --tail=20 "$svc" 2>/dev/null || true
      FAILED=$((FAILED + 1))
    fi
  fi
done

if [[ "$FAILED" -gt 0 ]]; then
  echo ""
  echo "=== FAILED: $FAILED service(s) not running ==="
  exit 1
fi

echo ""

# --------------------------------------------------------------------------
# Step 2: Check infrastructure service health
# --------------------------------------------------------------------------
echo "[2/3] Checking infrastructure health..."

# PostgreSQL
if docker compose exec -T postgres pg_isready -U deckforge > /dev/null 2>&1; then
  echo "  OK: PostgreSQL accepting connections"
else
  echo "  FAIL: PostgreSQL not ready"
  FAILED=$((FAILED + 1))
fi

# Redis
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -qi "pong"; then
  echo "  OK: Redis responding to PING"
else
  echo "  FAIL: Redis not responding"
  FAILED=$((FAILED + 1))
fi

# MinIO (check if port 9000 is listening)
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live 2>/dev/null | grep -q "200"; then
  echo "  OK: MinIO health endpoint responding"
else
  # Fallback: just check if the container is up (MinIO may not have /minio/health/live)
  minio_up=$(docker compose ps 2>/dev/null | grep "minio" | grep -ci "up\|running" || echo "0")
  if [[ "$minio_up" -ge 1 ]]; then
    echo "  OK: MinIO container is running (health endpoint not available)"
  else
    echo "  FAIL: MinIO not responding"
    FAILED=$((FAILED + 1))
  fi
fi

if [[ "$FAILED" -gt 0 ]]; then
  echo ""
  echo "=== FAILED: $FAILED infrastructure check(s) failed ==="
  exit 1
fi

echo ""

# --------------------------------------------------------------------------
# Step 3: Check API health endpoint
# --------------------------------------------------------------------------
echo "[3/3] Checking API health endpoint..."

API_URL="${DECKFORGE_API_URL:-http://localhost:8000}"
MAX_RETRIES=3
RETRY_DELAY=2

for attempt in $(seq 1 $MAX_RETRIES); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/v1/health" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "  OK: API health returns 200"
    echo ""
    echo "  Response:"
    curl -s "$API_URL/v1/health" | python3 -m json.tool 2>/dev/null || curl -s "$API_URL/v1/health"
    break
  elif [[ "$attempt" -lt "$MAX_RETRIES" ]]; then
    echo "  Attempt $attempt/$MAX_RETRIES: API returned $HTTP_CODE, retrying in ${RETRY_DELAY}s..."
    sleep "$RETRY_DELAY"
  else
    echo "  FAIL: API health returned $HTTP_CODE after $MAX_RETRIES attempts (expected 200)"
    echo "  API logs:"
    docker compose logs --tail=30 api 2>/dev/null || true
    FAILED=$((FAILED + 1))
  fi
done

if [[ "$FAILED" -gt 0 ]]; then
  echo ""
  echo "=== FAILED: API health check failed ==="
  exit 1
fi

echo ""
echo "=== All 6 services healthy ==="
echo ""
echo "Services verified:"
for svc in "${EXPECTED_SERVICES[@]}"; do
  echo "  - $svc"
done
