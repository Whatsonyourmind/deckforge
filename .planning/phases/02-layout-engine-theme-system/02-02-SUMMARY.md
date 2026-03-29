---
phase: 02-layout-engine-theme-system
plan: 02
subsystem: themes
tags: [pydantic, yaml, wcag, contrast, brand-kit, design-tokens, theme-system]

requires:
  - phase: 01-foundation-ir-schema
    provides: BrandKit, BrandColors, BrandFonts, LogoConfig, FooterConfig IR models

provides:
  - ResolvedTheme Pydantic model with colors, typography, spacing, slide_masters
  - ThemeResolver for $variable reference resolution with cycle detection
  - ContrastChecker with WCAG AA validation (W3C G18 algorithm)
  - BrandKitMerger for brand kit overlay with protected keys
  - ThemeRegistry loading/caching 15 YAML themes from data directory
  - 15 curated YAML themes with 3-tier design tokens

affects: [02-layout-engine-theme-system/plan-03, 03-pptx-renderer, 04-content-pipeline]

tech-stack:
  added: [pyyaml (existing), pydantic (existing)]
  patterns: [3-tier design tokens (colors/palette/slide_masters), $variable resolution, WCAG AA contrast validation, protected key merge pattern]

key-files:
  created:
    - src/deckforge/themes/__init__.py
    - src/deckforge/themes/types.py
    - src/deckforge/themes/resolver.py
    - src/deckforge/themes/contrast.py
    - src/deckforge/themes/brand_kit_merger.py
    - src/deckforge/themes/registry.py
    - src/deckforge/themes/data/executive-dark.yaml
    - src/deckforge/themes/data/corporate-blue.yaml
    - src/deckforge/themes/data/minimal-light.yaml
    - src/deckforge/themes/data/modern-gradient.yaml
    - src/deckforge/themes/data/warm-earth.yaml
    - src/deckforge/themes/data/tech-neon.yaml
    - src/deckforge/themes/data/classic-serif.yaml
    - src/deckforge/themes/data/bold-impact.yaml
    - src/deckforge/themes/data/soft-pastel.yaml
    - src/deckforge/themes/data/monochrome.yaml
    - src/deckforge/themes/data/ocean-depth.yaml
    - src/deckforge/themes/data/forest-green.yaml
    - src/deckforge/themes/data/sunset-warm.yaml
    - src/deckforge/themes/data/arctic-clean.yaml
    - src/deckforge/themes/data/finance-pro.yaml
    - tests/unit/test_theme_registry.py
    - tests/unit/test_theme_colors.py
    - tests/unit/test_brand_kit.py
  modified: []

key-decisions:
  - "3-tier design token YAML structure: colors (raw hex) -> palette (semantic $refs) -> slide_masters ($ref to palette)"
  - "ThemeResolver processes tiers in order (colors, palette, then rest) to avoid order-dependent resolution bugs"
  - "BrandKitMerger returns new ResolvedTheme (immutable pattern) with protected keys: spacing, typography.scale, typography.line_height"
  - "ContrastChecker validates but does not reject — logs warnings for WCAG AA failures during theme loading"
  - "LogoDefaults and FooterDefaults Pydantic models added to ResolvedTheme for renderer consumption"

patterns-established:
  - "3-tier design tokens: Tier 1 (raw colors), Tier 2 (semantic palette via $refs), Tier 3 (slide_masters via $refs)"
  - "Protected key pattern: BrandKitMerger skips spacing/scale/line_height to prevent layout breakage"
  - "Theme YAML contract: name, description, version, colors, palette, typography, spacing, slide_masters (10+), chart_colors, logo, _protected"
  - "WCAG AA contrast validation: 4.5:1 for body text, 3:1 for large text"

requirements-completed: [THEME-01, THEME-02, THEME-03, THEME-04, THEME-05]

duration: 9min
completed: 2026-03-29
---

# Phase 2 Plan 2: Theme System Summary

**15 curated YAML themes with 3-tier design tokens, $variable resolution with cycle detection, WCAG AA contrast validation, and brand kit overlay with protected keys**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-29T01:08:16Z
- **Completed:** 2026-03-29T01:17:33Z
- **Tasks:** 2
- **Files created:** 24

## Accomplishments

- Built complete theme type system: ThemeColors, ThemeTypography, ThemeSpacing, ComponentStyle, SlideMaster, ResolvedTheme Pydantic models
- ThemeResolver resolves $variable references across 3-tier YAML structure with circular reference detection
- ContrastChecker validates WCAG AA compliance using W3C G18 sRGB linearization algorithm
- BrandKitMerger applies brand colors/fonts overlay while protecting structural properties (spacing, scale, line_height)
- ThemeRegistry loads, resolves, validates, and caches 15 YAML themes with integrated brand kit support
- 15 visually distinct themes spanning dark, light, serif, bold, pastel, monochrome, and domain-specific (finance) styles
- All 15 themes pass WCAG AA contrast validation for text on backgrounds

## Task Commits

Each task was committed atomically:

1. **Task 1: Theme types, ThemeResolver, and ContrastChecker (TDD)**
   - `70207d4` (test) — RED: failing tests for resolver and contrast checker
   - `8cb3a01` (feat) — GREEN: implement types, resolver, contrast checker — 25 tests pass
2. **Task 2: 15 YAML themes, ThemeRegistry, and BrandKitMerger**
   - `2c55a61` (feat) — 15 YAML themes, registry, merger, tests — 49 tests pass

## Files Created/Modified

- `src/deckforge/themes/__init__.py` — Package exports: ResolvedTheme, ThemeResolver, ContrastChecker, BrandKitMerger, ThemeRegistry
- `src/deckforge/themes/types.py` — Pydantic models: ThemeColors, ThemeTypography, ThemeSpacing, ComponentStyle, SlideMaster, ResolvedTheme
- `src/deckforge/themes/resolver.py` — ThemeResolver: $variable resolution with cycle detection, 3-tier ordering
- `src/deckforge/themes/contrast.py` — WCAG AA: hex_to_rgb, relative_luminance, contrast_ratio, passes_wcag_aa, validate_theme_contrast
- `src/deckforge/themes/brand_kit_merger.py` — BrandKitMerger: deep merge with protected keys, immutable returns
- `src/deckforge/themes/registry.py` — ThemeRegistry: YAML loading, resolution, caching, brand kit integration, validate_all
- `src/deckforge/themes/data/*.yaml` — 15 curated themes (executive-dark, corporate-blue, minimal-light, modern-gradient, warm-earth, tech-neon, classic-serif, bold-impact, soft-pastel, monochrome, ocean-depth, forest-green, sunset-warm, arctic-clean, finance-pro)
- `tests/unit/test_theme_registry.py` — ThemeResolver tests (7) + ResolvedTheme model tests (2)
- `tests/unit/test_theme_colors.py` — ContrastChecker tests (14): hex_to_rgb, luminance, ratio, WCAG AA, validate_theme_contrast
- `tests/unit/test_brand_kit.py` — BrandKitMerger tests (15) + ThemeRegistry tests (9)

## Decisions Made

- **3-tier design token YAML structure**: colors (Tier 1, raw hex) -> palette (Tier 2, semantic $refs) -> slide_masters (Tier 3, $refs to palette). This matches the research-recommended pattern and enables theme switching by only changing Tier 1.
- **Tier-ordered resolution**: ThemeResolver processes colors first, then palette, then everything else to guarantee references resolve correctly regardless of YAML key ordering.
- **Immutable merge pattern**: BrandKitMerger returns a new ResolvedTheme, never mutates the original. This prevents cache corruption in ThemeRegistry.
- **Protected keys**: spacing, typography.scale, and typography.line_height cannot be overridden by brand kit to prevent layout breakage when different brands use the same theme.
- **Validate but don't reject**: ContrastChecker logs warnings during theme loading but doesn't prevent loading. This allows flexibility while surfacing accessibility issues.
- **LogoDefaults and FooterDefaults models**: Added to ResolvedTheme to carry theme-level logo/footer defaults for renderer consumption, separate from BrandKit overlay.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Theme system is complete and ready for consumption by the layout engine (Plan 03) and PPTX renderer (Phase 3)
- ResolvedTheme provides all data needed for slide styling: colors, fonts, spacing, per-slide-type masters
- ThemeRegistry.get_theme() is the single entry point for themed slide generation
- BrandKitMerger integrates with the BrandKit IR model from Phase 1
- All 49 unit tests provide regression safety for future changes

## Self-Check: PASSED

- All 24 created files exist on disk
- All 3 task commits verified in git history (70207d4, 8cb3a01, 2c55a61)
- 49/49 tests passing

---
*Phase: 02-layout-engine-theme-system*
*Completed: 2026-03-29*
