# Phase 7 Research: QA Pipeline + Deck Operations

**Researched:** 2026-03-26
**Phase:** 07-qa-pipeline-deck-operations
**Requirements:** QA-01..07, DECK-01..07, BATCH-01..02, API-04, API-12

---

## 1. Text Overflow Detection

### Problem
After rendering, text may still overflow its bounding box despite the layout engine's adaptive cascade. The QA pipeline needs to independently verify rendered output.

### Approach: Post-Layout Measurement Verification
The layout engine already uses `TextMeasurer` (Pillow + FreeType) to compute bounding boxes before rendering. The QA pass re-measures text in each element against its allocated position from `LayoutResult`.

**Implementation:**
```python
class TextOverflowChecker:
    """Compares rendered text dimensions against allocated bounding boxes."""

    def check_slide(self, slide: BaseSlide, layout: LayoutResult, theme: ResolvedTheme) -> list[QAIssue]:
        issues = []
        for region_name, position in layout.positions.items():
            text = extract_region_text(slide, region_name)
            if text is None:
                continue
            style = get_region_style(region_name, slide.slide_type, theme)
            measured = measurer.measure_text(text, style.font_family, style.font_size, max_width_inches=position.width)
            if measured.height_inches > position.height + TOLERANCE:
                issues.append(QAIssue(
                    type="text_overflow",
                    severity="error",
                    slide_index=...,
                    region=region_name,
                    measured_height=measured.height_inches,
                    allocated_height=position.height,
                ))
        return issues
```

**Key detail:** Reuse the existing `TextMeasurer` and `AdaptiveOverflowHandler.detect_overflow()` logic from `src/deckforge/layout/overflow.py`. The QA pass is a second measurement pass after all rendering decisions are finalized.

**Tolerance:** 0.01 inches (same as existing overflow detection in `overflow.py` line 70).

### Orphan/Widow Detection
- Orphan: single word on last line of a paragraph
- Widow: single line of a paragraph at top of next slide (after split)
- Detection: re-measure text, count lines, check if last line has <2 words

---

## 2. WCAG AA Automated Checking on Rendered Output

### Existing Infrastructure
The codebase already has a complete WCAG AA contrast checker at `src/deckforge/themes/contrast.py`:
- `hex_to_rgb()`, `relative_luminance()`, `contrast_ratio()`, `passes_wcag_aa()`
- `validate_theme_contrast()` checks theme-level colors
- Currently used during theme loading (warns but does not reject)

### QA Extension: Per-Element Contrast Checking
The theme-level check validates text_primary/text_secondary against background/surface. The QA pipeline extends this to per-element checking:

1. **Every text element** on every slide: resolve the actual foreground color (from element style override or theme default) and the actual background color (from slide master, slide background, or underlying shape)
2. **Font size context:** Text >=18pt or >=14pt bold is "large text" (3:1 threshold), otherwise 4.5:1
3. **Chart labels:** Verify chart axis labels and data labels against chart background

**Implementation:** Walk all elements, resolve fg/bg colors via theme cascade, call `passes_wcag_aa()` for each pair.

### Font Size Floor Enforcement
- Body text: minimum 10pt (already enforced in overflow handler)
- Footnotes: minimum 8pt
- Chart labels: minimum 9pt
- QA flags any text below these floors

### Alignment Consistency
- Verify left-edge alignment within +-2px tolerance (existing LAYOUT-05 constraint)
- Check vertical spacing consistency between elements on same slide

---

## 3. Auto-Fix Strategies

### Font Reduction (text overflow fix)
Already implemented in `AdaptiveOverflowHandler`. QA auto-fix re-invokes the same cascade:
1. Reduce font by 2pt steps (min 10pt body / 14pt heading)
2. Reflow with 90% width
3. If still overflowing, flag as unfixable (splitting requires re-rendering)

### Contrast Adjustment
When contrast ratio fails:
1. **Lighten or darken the text color** to meet threshold
2. Algorithm: binary search between current fg color and black/white to find the nearest color that passes
3. Never modify background (too invasive) -- only adjust text color
4. Record the original and adjusted colors in the QA report

```python
def fix_contrast(fg_hex: str, bg_hex: str, target_ratio: float = 4.5) -> str:
    """Adjust fg color toward black or white until contrast passes."""
    bg_rgb = hex_to_rgb(bg_hex)
    bg_lum = relative_luminance(*bg_rgb)
    # If background is dark, lighten text toward white; if light, darken toward black
    target = (255, 255, 255) if bg_lum < 0.5 else (0, 0, 0)
    # Binary search for minimum adjustment
    ...
```

### Spacing Correction
When alignment is off:
1. Snap elements to nearest grid column boundary
2. Enforce minimum gutter (from theme.spacing.gutter)
3. Adjust element_gap to match theme.spacing.element_gap

### Data Integrity Fixes
- Percentages not summing to 100: flag but do NOT auto-fix (data is authoritative)
- Table totals: recalculate sum, flag mismatch, optionally update if within rounding error

---

## 4. Executive Readiness Scoring Algorithm

### Scoring Model (0-100)

Five weighted categories, each scored 0-20:

| Category | Weight | What it measures |
|----------|--------|------------------|
| Structural Integrity | 20 | Title presence, no empty slides, narrative flow |
| Text Quality | 20 | No overflow, no orphans, consistent capitalization |
| Visual Quality | 20 | WCAG AA contrast, font size floors, alignment |
| Data Integrity | 20 | Chart data matches, table totals, percentage sums |
| Brand Compliance | 20 | Approved colors/fonts, logo placement, confidentiality |

### Scoring Rules

Each category starts at 20 and deducts points per issue:

```python
DEDUCTIONS = {
    # Structural (20 points)
    "missing_title": -5,
    "empty_slide": -10,
    "no_narrative_flow": -3,

    # Text Quality (20 points)
    "text_overflow": -5,
    "orphan_word": -2,
    "inconsistent_capitalization": -2,

    # Visual (20 points)
    "contrast_failure": -5,
    "font_below_floor": -3,
    "alignment_off": -2,

    # Data (20 points)
    "percentage_sum_wrong": -5,
    "table_total_mismatch": -5,
    "chart_data_mismatch": -5,

    # Brand (20 points)
    "unapproved_color": -3,
    "unapproved_font": -3,
    "missing_logo": -5,
    "missing_confidentiality": -3,
}
```

**Floor:** Minimum 0 per category. Total = sum of five categories.

### Threshold Classification
- 90-100: "Executive Ready" -- ship as-is
- 70-89: "Review Recommended" -- minor issues found
- 50-69: "Needs Attention" -- significant issues
- 0-49: "Not Ready" -- critical failures

---

## 5. Deck Composability (Append/Replace/Reorder/Retheme)

### Architecture: Operations on Stored IR

All deck operations work on the IR (JSON) stored in `decks.ir_snapshot`, not on the rendered PPTX. This gives us:
1. Lossless modification (no information lost in round-trip)
2. Re-rendering after modification using the existing pipeline
3. Full reproducibility via stored IR

### Deck CRUD

Existing infrastructure:
- `DeckRepository` with `get_by_id`, `create`, `update_status` (in `db/repositories/deck.py`)
- `Deck` model with `ir_snapshot` (JSON column), `file_url`, `quality_score`

New endpoints:
```
GET    /v1/decks              -- List decks (paginated, filtered by api_key)
GET    /v1/decks/{id}         -- Get deck metadata + download_url
GET    /v1/decks/{id}/ir      -- Get the IR that produced the deck
DELETE /v1/decks/{id}         -- Soft-delete a deck
```

### Slide Operations

All mutation endpoints accept the deck ID and return the modified deck:

```
POST   /v1/decks/{id}/append    -- Append slides (IR slide objects)
PUT    /v1/decks/{id}/slides/{index} -- Replace slide at index
POST   /v1/decks/{id}/reorder   -- Reorder slides (new index list)
POST   /v1/decks/{id}/retheme   -- Apply new theme to entire deck
POST   /v1/decks/{id}/export    -- Re-export to different format
```

**Pattern:** Each mutation:
1. Loads IR from `ir_snapshot`
2. Modifies the IR (append/replace/reorder/theme change)
3. Re-validates via Pydantic
4. Re-renders via `render_pipeline()`
5. Stores updated IR + new file_url
6. Returns updated deck metadata

### Retheme Implementation
Change `presentation.theme` in IR, then re-render. The theme engine + layout engine handle all cascade effects automatically.

---

## 6. Batch Rendering with ARQ Fan-Out

### Pattern: Batch Job -> Individual Sub-Jobs

```
POST /v1/batch/render
{
    "items": [
        {"ir": {...}, "theme": "executive-dark"},
        {"ir": {...}, "theme": "minimal-light"}
    ]
}
```

**Response:**
```json
{
    "batch_id": "batch_xxx",
    "jobs": [
        {"job_id": "job_1", "status": "queued"},
        {"job_id": "job_2", "status": "queued"}
    ]
}
```

### Fan-Out Architecture
1. API creates a `BatchJob` record (parent)
2. For each item, creates an individual `Job` record with `batch_id` foreign key
3. Each individual job is enqueued to ARQ independently
4. Workers process in parallel (naturally distributed across worker pool)
5. A completion checker task runs after each sub-job completes:
   - Query all jobs with this `batch_id`
   - If all complete -> update batch status, fire webhook

### Theme Variations (BATCH-02)
Syntactic sugar: provide one IR + list of themes. Expands to N individual render jobs.

```
POST /v1/batch/variations
{
    "ir": {...},
    "themes": ["executive-dark", "minimal-light", "corporate-blue"]
}
```

Internally converts to N batch items with same IR + different theme.

### Database Model Addition
```python
class BatchJob(Base):
    __tablename__ = "batch_jobs"
    id: Mapped[uuid.UUID]
    api_key_id: Mapped[uuid.UUID]
    total_items: Mapped[int]
    completed_items: Mapped[int] = 0
    status: Mapped[str] = "pending"  # pending, running, complete, partial_failure
    webhook_url: Mapped[str | None]
```

---

## 7. Webhook Delivery Patterns

### Existing Implementation
`src/deckforge/workers/webhooks.py` already has `deliver_webhook()` with:
- httpx async POST
- Exponential backoff retry (1s, 2s, 4s)
- 3 max retries
- 10s timeout

### Enhancements Needed for API-12

**Webhook Registration:**
```
POST /v1/webhooks
{
    "url": "https://example.com/webhook",
    "events": ["render.complete", "generate.complete", "batch.complete"],
    "secret": "whsec_..."  // Optional: user-provided or auto-generated
}
```

**Signature Verification (HMAC-SHA256):**
```python
import hashlib, hmac, time

def sign_webhook(payload_bytes: bytes, secret: str, timestamp: int) -> str:
    message = f"{timestamp}.{payload_bytes.decode()}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

# Include in headers:
# X-DeckForge-Signature: t=1234567890,v1=<hmac>
# X-DeckForge-Timestamp: 1234567890
```

**Retry with Dead Letter:**
- Current: 3 retries with exponential backoff (sufficient for MVP)
- Enhancement: Store delivery attempts in DB for debugging
- Enhancement: After max retries, mark as failed (dead letter)
- User can query failed deliveries via API

**Webhook Events:**
- `render.complete` -- single deck rendered
- `generate.complete` -- content generation + render done
- `batch.complete` -- all items in batch done
- `render.failed` / `generate.failed` / `batch.failed`

---

## 8. Cost Estimation from IR Metadata

### Credit Cost Model (from BILL-02)

Base: 1 credit per 10-slide structured render.

**Calculation:**
```python
def estimate_credits(ir: Presentation) -> CostEstimate:
    slide_count = len(ir.slides)
    base_credits = math.ceil(slide_count / 10)

    surcharges = {}

    # Finance slide surcharge: +0.5 per finance slide
    finance_types = {"comp_table", "dcf_summary", "waterfall_chart", ...}
    finance_count = sum(1 for s in ir.slides if s.slide_type in finance_types)
    if finance_count > 0:
        surcharges["finance"] = finance_count * 0.5

    # Chart surcharge: +0.2 per chart element
    chart_count = count_chart_elements(ir)
    if chart_count > 0:
        surcharges["charts"] = chart_count * 0.2

    total = base_credits + sum(surcharges.values())
    return CostEstimate(base=base_credits, surcharges=surcharges, total=math.ceil(total))
```

**Endpoint:**
```
POST /v1/estimate
{
    "ir": {...}  // or "prompt": "..." for NL estimation
}
```

For NL prompts, estimate based on generation_options.target_slide_count or a default of 10.

---

## Plan Architecture

### Plan 07-01 (Wave 1): QA Pipeline + Auto-Fix + Scoring
**Requirements:** QA-01, QA-02, QA-03, QA-04, QA-05, QA-06, QA-07

Files:
- `src/deckforge/qa/__init__.py`
- `src/deckforge/qa/types.py` -- QAIssue, QAReport, QACategory models
- `src/deckforge/qa/checkers/structural.py` -- QA-01
- `src/deckforge/qa/checkers/text.py` -- QA-02
- `src/deckforge/qa/checkers/visual.py` -- QA-03
- `src/deckforge/qa/checkers/data.py` -- QA-04
- `src/deckforge/qa/checkers/brand.py` -- QA-05
- `src/deckforge/qa/autofix.py` -- QA-06
- `src/deckforge/qa/scorer.py` -- QA-07
- `src/deckforge/qa/pipeline.py` -- Orchestrates 5 checks + autofix + scoring

### Plan 07-02 (Wave 1): Deck Operations + Cost Estimation
**Requirements:** DECK-01, DECK-02, DECK-03, DECK-04, DECK-05, DECK-06, DECK-07, API-04

Files:
- `src/deckforge/api/routes/decks.py` -- CRUD + mutation endpoints
- `src/deckforge/api/routes/estimate.py` -- POST /v1/estimate
- `src/deckforge/api/schemas/deck_schemas.py` -- Request/response models
- `src/deckforge/services/deck_ops.py` -- Append/replace/reorder/retheme/export logic
- `src/deckforge/services/cost_estimator.py` -- Credit estimation

### Plan 07-03 (Wave 2): Batch Operations + Webhooks + Wire
**Requirements:** BATCH-01, BATCH-02, API-12

Files:
- `src/deckforge/db/models/batch_job.py` -- BatchJob model
- `src/deckforge/db/models/webhook.py` -- WebhookRegistration model
- `src/deckforge/db/repositories/batch.py` -- BatchJob repo
- `src/deckforge/db/repositories/webhook.py` -- Webhook repo
- `src/deckforge/api/routes/batch.py` -- Batch endpoints
- `src/deckforge/api/routes/webhooks.py` -- Webhook registration endpoints
- `src/deckforge/workers/webhooks.py` -- Enhanced with HMAC signing + delivery tracking
- `src/deckforge/workers/tasks.py` -- Wire QA pipeline into render_pipeline
- Alembic migration for batch_jobs and webhook_registrations tables

---

## Sources

- Existing codebase: `src/deckforge/layout/overflow.py` (overflow detection + adaptive cascade)
- Existing codebase: `src/deckforge/themes/contrast.py` (WCAG AA checker)
- Existing codebase: `src/deckforge/workers/webhooks.py` (basic webhook delivery)
- Existing codebase: `src/deckforge/db/repositories/deck.py` (deck CRUD)
- WCAG 2.1 AA Guidelines: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Stripe webhook signature verification pattern: https://docs.stripe.com/webhooks/signatures
- ARQ task queue documentation: https://arq-docs.helpmanual.io/
