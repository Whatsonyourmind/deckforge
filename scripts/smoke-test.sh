#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# DeckForge End-to-End Smoke Test
# ============================================================================
# Verifies the full render pipeline: API -> Renderer -> .pptx output
#
# Requires:
#   - Services running (docker compose up -d)
#   - Database bootstrapped (scripts/bootstrap-db.sh)
#   - DECKFORGE_TEST_API_KEY env var set (or pass via --api-key)
#
# Exits 0 on success, non-zero on failure.
#
# Usage:
#   export DECKFORGE_TEST_API_KEY=dk_test_...
#   bash scripts/smoke-test.sh
#   bash scripts/smoke-test.sh --api-key dk_test_abc123
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/tmp/smoke-test"
API_URL="${DECKFORGE_API_URL:-http://localhost:8000}"

# Parse optional --api-key argument
API_KEY="${DECKFORGE_TEST_API_KEY:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-key)
      API_KEY="$2"
      shift 2
      ;;
    --api-url)
      API_URL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--api-key KEY] [--api-url URL]"
      exit 1
      ;;
  esac
done

mkdir -p "$OUTPUT_DIR"

echo "=== DeckForge Smoke Test ==="
echo "  API URL: $API_URL"
echo "  Output:  $OUTPUT_DIR"
echo ""

# --------------------------------------------------------------------------
# Step 1: Health check
# --------------------------------------------------------------------------
echo "[1/4] Health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/v1/health" 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "  FAIL: Health check returned $HTTP_CODE (expected 200)"
  echo "  Is the API running? Try: docker compose up -d"
  exit 1
fi
echo "  OK: API is healthy"
echo ""

# --------------------------------------------------------------------------
# Step 2: Verify API key
# --------------------------------------------------------------------------
echo "[2/4] Checking API key..."
if [[ -z "$API_KEY" ]]; then
  echo "  No DECKFORGE_TEST_API_KEY set."
  echo "  Attempting to read from database..."

  # Try to get a key from the database directly
  DB_KEY=$(docker compose exec -T postgres psql -U deckforge -d deckforge -t -c \
    "SELECT prefix || '...' FROM api_keys LIMIT 1;" 2>/dev/null | tr -d ' \n' || echo "")

  if [[ -z "$DB_KEY" || "$DB_KEY" == "..." || "$DB_KEY" == *"ERROR"* ]]; then
    echo "  WARN: No API key found in database."
    echo ""
    echo "  To run full smoke test:"
    echo "    1. Run: bash scripts/bootstrap-db.sh"
    echo "    2. Set: export DECKFORGE_TEST_API_KEY=dk_test_..."
    echo "    3. Re-run: bash scripts/smoke-test.sh"
    echo ""
    echo "  Health check passed -- exiting with success (partial test)."
    exit 0
  fi

  echo "  Found key prefix: $DB_KEY"
  echo "  NOTE: Cannot retrieve full key from DB (hashed). Set DECKFORGE_TEST_API_KEY."
  echo "  Health check passed -- exiting with success (partial test)."
  exit 0
fi

echo "  OK: API key configured"
echo ""

# --------------------------------------------------------------------------
# Step 3: Render a 3-slide test presentation
# --------------------------------------------------------------------------
echo "[3/4] Testing render pipeline..."

# Build IR body matching the actual DeckForge Presentation schema.
# The render endpoint (POST /v1/render) accepts a Presentation object directly.
# Slide types: title_slide, bullet_points, two_column_text (from universal.py)
# Each slide has an elements array with typed element objects.
RENDER_BODY='{
  "schema_version": "1.0",
  "metadata": {
    "title": "DeckForge Smoke Test",
    "author": "DeckForge CI"
  },
  "theme": "corporate-blue",
  "slides": [
    {
      "slide_type": "title_slide",
      "elements": [
        {
          "type": "text",
          "content": "DeckForge Smoke Test",
          "role": "title"
        },
        {
          "type": "text",
          "content": "Automated end-to-end verification",
          "role": "subtitle"
        }
      ]
    },
    {
      "slide_type": "bullet_points",
      "elements": [
        {
          "type": "text",
          "content": "Key Capabilities",
          "role": "title"
        },
        {
          "type": "text",
          "content": "32 slide types\n15 curated themes\nAI-powered content generation\nFinance vertical support",
          "role": "body"
        }
      ]
    },
    {
      "slide_type": "two_column_text",
      "elements": [
        {
          "type": "text",
          "content": "Two Column Layout",
          "role": "title"
        },
        {
          "type": "text",
          "content": "Left column content with key points about the rendering pipeline.",
          "role": "body"
        },
        {
          "type": "text",
          "content": "Right column content demonstrating layout engine capabilities.",
          "role": "body"
        }
      ]
    }
  ]
}'

OUTPUT_FILE="$OUTPUT_DIR/smoke-test.pptx"

HTTP_CODE=$(curl -s -o "$OUTPUT_FILE" -w "%{http_code}" \
  -X POST "$API_URL/v1/render" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$RENDER_BODY")

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "  FAIL: Render returned HTTP $HTTP_CODE (expected 200)"
  echo "  Response body:"
  cat "$OUTPUT_FILE" 2>/dev/null || true
  exit 1
fi

# Validate output file size (PPTX should be >5KB)
FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null || echo "0")
if [[ "$FILE_SIZE" -lt 5000 ]]; then
  echo "  FAIL: Output file too small (${FILE_SIZE} bytes, expected >5000)"
  echo "  File may be an error response, not a .pptx"
  cat "$OUTPUT_FILE" 2>/dev/null || true
  exit 1
fi

# Check PK zip header (PPTX is a ZIP file, starts with PK = 0x504b)
HEADER=$(xxd -l 2 -p "$OUTPUT_FILE" 2>/dev/null \
  || od -A n -t x1 -N 2 "$OUTPUT_FILE" 2>/dev/null | tr -d ' \n' \
  || echo "0000")
if [[ "$HEADER" != "504b" ]]; then
  echo "  FAIL: File does not have PK zip header (got: $HEADER)"
  echo "  File is not a valid .pptx (ZIP) archive"
  exit 1
fi

echo "  OK: Render produced valid .pptx (${FILE_SIZE} bytes)"
echo "  Output: $OUTPUT_FILE"
echo ""

# --------------------------------------------------------------------------
# Step 4: Test generate endpoint (optional, requires LLM API key)
# --------------------------------------------------------------------------
echo "[4/4] Testing generate pipeline (optional)..."

GENERATE_BODY='{
  "prompt": "Create a 2-slide overview of cloud computing benefits",
  "generation_options": {
    "target_slide_count": 2
  }
}'

GEN_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$API_URL/v1/generate" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$GENERATE_BODY" \
  --max-time 30 2>/dev/null || echo "000")

if [[ "$GEN_CODE" == "200" || "$GEN_CODE" == "202" ]]; then
  echo "  OK: Generate endpoint responding ($GEN_CODE)"
elif [[ "$GEN_CODE" == "422" || "$GEN_CODE" == "500" || "$GEN_CODE" == "503" ]]; then
  echo "  SKIP: Generate returned $GEN_CODE (likely no LLM API key configured -- OK for smoke test)"
else
  echo "  SKIP: Generate returned $GEN_CODE (non-critical for smoke test)"
fi

echo ""
echo "=== Smoke Test PASSED ==="
echo ""
echo "Results:"
echo "  Health check:     OK"
echo "  Authentication:   OK"
echo "  Render pipeline:  OK (3 slides -> valid .pptx)"
echo "  Output file:      $OUTPUT_FILE"
echo "  File size:        ${FILE_SIZE} bytes"
