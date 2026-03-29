---
phase: 05-chart-engine-finance-vertical
plan: 01
subsystem: charts
tags: [plotly, kaleido, pptx, png, static-charts, chart-recommender, waterfall, heatmap, sankey, gantt]

# Dependency graph
requires:
  - phase: 03-pptx-rendering
    provides: BaseChartRenderer, PlaceholderChartRenderer, CHART_RENDERERS registry, python-pptx rendering pipeline
provides:
  - StaticChartRenderer base class for Plotly-to-PNG-to-PPTX rendering
  - 10 static chart renderers (waterfall, heatmap, sankey, gantt, football_field, sensitivity, funnel, treemap, tornado, sunburst)
  - Updated CHART_RENDERERS registry with zero placeholder entries
  - Chart type recommender (recommend_chart_type) with decision tree
affects: [05-chart-engine-finance-vertical, 06-google-slides-output]

# Tech tracking
tech-stack:
  added: [plotly>=6.1, kaleido>=1.0.0, pandas (transitive via plotly.express)]
  patterns: [StaticChartRenderer abstract base for Plotly charts, Plotly figure-to-PNG-to-PPTX pipeline, rule-based chart recommendation with confidence scores]

key-files:
  created:
    - src/deckforge/rendering/chart_renderers/static_base.py
    - src/deckforge/rendering/chart_renderers/waterfall.py
    - src/deckforge/rendering/chart_renderers/heatmap.py
    - src/deckforge/rendering/chart_renderers/sankey.py
    - src/deckforge/rendering/chart_renderers/gantt.py
    - src/deckforge/rendering/chart_renderers/football_field.py
    - src/deckforge/rendering/chart_renderers/sensitivity.py
    - src/deckforge/rendering/chart_renderers/funnel.py
    - src/deckforge/rendering/chart_renderers/treemap.py
    - src/deckforge/rendering/chart_renderers/tornado.py
    - src/deckforge/rendering/chart_renderers/sunburst.py
    - src/deckforge/charts/__init__.py
    - src/deckforge/charts/recommender.py
    - tests/unit/test_static_chart_renderers.py
    - tests/unit/test_chart_recommender.py
  modified:
    - pyproject.toml
    - src/deckforge/rendering/chart_renderers/__init__.py
    - tests/unit/test_chart_renderers.py

key-decisions:
  - "StaticChartRenderer uses 150 DPI base * scale=2 for 300 effective DPI PNG export"
  - "Transparent background (rgba(0,0,0,0)) for plotly charts to blend with slide backgrounds"
  - "Gantt renderer imports pandas locally inside _build_figure() to avoid import-time dependency"
  - "Waterfall _infer_measures() uses heuristic keyword match on last category for total detection"
  - "ChartRecommendation is a frozen dataclass with chart_type, confidence (0-1), and reason"

patterns-established:
  - "StaticChartRenderer: abstract _build_figure() -> go.Figure, base handles PNG export and PPTX embedding"
  - "Chart recommender decision tree: specialized types (high priority) -> standard types (series/category counts) -> bar default"

requirements-completed: [CHART-01, CHART-02, CHART-03, CHART-04, CHART-05]

# Metrics
duration: 9min
completed: 2026-03-29
---

# Phase 5 Plan 01: Static Chart Engine Summary

**Plotly-based static chart renderers for 10 chart types (waterfall through sunburst) replacing all placeholder rectangles with high-res PNG images, plus rule-based chart type recommender**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-29T02:19:06Z
- **Completed:** 2026-03-29T02:28:09Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- All 10 previously-placeholder chart types now render as real Plotly PNG images in PPTX slides
- StaticChartRenderer base class provides shared Plotly-to-PNG-to-PPTX pipeline with theme integration
- Chart recommender maps 11 data shape patterns to appropriate chart types with confidence scores
- Zero PlaceholderChartRenderer entries remain in the CHART_RENDERERS registry
- 69 total chart tests passing (40 existing + 13 new static + 16 recommender)

## Task Commits

Each task was committed atomically:

1. **Task 1: Static chart base class and Plotly renderers** - TDD workflow
   - `6cb0f6c` (test: add failing tests for static chart renderers)
   - `849cebb` (feat: implement Plotly-based static chart renderers for all 10 chart types)

2. **Task 2: Chart type recommender** - TDD workflow
   - `e4103d1` (test: add failing tests for chart type recommender)
   - `02d89ab` (feat: implement chart type recommender with decision tree)

## Files Created/Modified
- `src/deckforge/rendering/chart_renderers/static_base.py` - Base class: Plotly figure -> PNG bytes -> PPTX picture shape
- `src/deckforge/rendering/chart_renderers/waterfall.py` - go.Waterfall with positive/negative/total coloring
- `src/deckforge/rendering/chart_renderers/heatmap.py` - go.Heatmap with theme colorscale and annotations
- `src/deckforge/rendering/chart_renderers/sankey.py` - go.Sankey with node index mapping and flow links
- `src/deckforge/rendering/chart_renderers/gantt.py` - px.timeline with reversed y-axis for project schedules
- `src/deckforge/rendering/chart_renderers/football_field.py` - Horizontal range bars with optional midpoint diamonds
- `src/deckforge/rendering/chart_renderers/sensitivity.py` - Annotated heatmap with row/col headers for DCF sensitivity
- `src/deckforge/rendering/chart_renderers/funnel.py` - go.Funnel with theme-cycled stage colors
- `src/deckforge/rendering/chart_renderers/treemap.py` - go.Treemap with parent hierarchy
- `src/deckforge/rendering/chart_renderers/tornado.py` - Overlapping horizontal bars with base_value offset
- `src/deckforge/rendering/chart_renderers/sunburst.py` - go.Sunburst with parent/label/value hierarchy
- `src/deckforge/charts/__init__.py` - Chart intelligence package marker
- `src/deckforge/charts/recommender.py` - Rule-based chart type recommender with ChartRecommendation dataclass
- `src/deckforge/rendering/chart_renderers/__init__.py` - Registry updated: 10 placeholders replaced with real renderers
- `pyproject.toml` - Added plotly>=6.1 and kaleido>=1.0.0 dependencies
- `tests/unit/test_static_chart_renderers.py` - 13 tests for static chart renderers
- `tests/unit/test_chart_recommender.py` - 16 tests for chart recommender
- `tests/unit/test_chart_renderers.py` - Updated placeholder tests to use PlaceholderChartRenderer directly

## Decisions Made
- StaticChartRenderer uses 150 DPI base with scale=2 for 300 effective DPI in exported PNG images
- Transparent background (rgba(0,0,0,0)) for all Plotly charts so they blend with slide backgrounds
- Gantt renderer imports pandas locally inside `_build_figure()` to avoid import-time dependency on pandas
- Waterfall `_infer_measures()` uses heuristic keyword match ("total", "net", "sum") on last category for total detection
- ChartRecommendation is a frozen dataclass (not Pydantic) since it's a simple output type with no validation needs
- Football field chart uses go.Bar with base parameter for range positioning, go.Scatter diamonds for midpoints
- Tornado chart uses barmode="overlay" with low values as-is (already negative) and high values for bidirectional bars

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing placeholder tests**
- **Found during:** Task 1 (static chart renderers implementation)
- **Issue:** Existing test_chart_renderers.py TestPlaceholderChartRenderer tests used CHART_RENDERERS["waterfall"] expecting a placeholder, but waterfall is now a real renderer
- **Fix:** Changed tests to instantiate PlaceholderChartRenderer directly instead of looking it up from registry
- **Files modified:** tests/unit/test_chart_renderers.py
- **Verification:** All 40 existing tests pass after fix
- **Committed in:** 849cebb (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary fix for test compatibility after replacing placeholders. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 10 static chart types render as real Plotly PNG images in PPTX
- Chart recommender ready for content pipeline integration (Phase 4)
- CHART_RENDERERS registry complete with all 24 chart types having real renderers
- Ready for 05-02 (finance data layer) and 05-03 (finance slide renderers)

## Self-Check: PASSED

- All 15 created files verified present on disk
- All 4 commit hashes verified in git log (6cb0f6c, 849cebb, e4103d1, 02d89ab)
- 69 tests passing across 3 test files

---
*Phase: 05-chart-engine-finance-vertical*
*Completed: 2026-03-29*
