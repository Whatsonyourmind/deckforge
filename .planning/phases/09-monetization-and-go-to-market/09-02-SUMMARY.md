---
phase: 09-monetization-and-go-to-market
plan: 02
subsystem: mcp, sdk, infra
tags: [mcp, fastmcp, npm, github-actions, ci-cd, marketing, open-source]

# Dependency graph
requires:
  - phase: 08-typescript-sdk-billing-launch
    provides: TypeScript SDK with builder API, billing tiers, slide type registry
provides:
  - MCP server with 6 tools for AI agent discovery (render, generate, themes, slide_types, cost_estimate, pricing)
  - GitHub Actions npm publish workflow on sdk-v* tag push
  - Marketing-grade SDK README (409 lines) with pricing, API reference, benchmarks
  - GitHub repo setup with issue templates and contribution guide
affects: [deployment, marketing, developer-experience]

# Tech tracking
tech-stack:
  added: [mcp, fastmcp]
  patterns: [mcp-tool-registration, lazy-import-pattern, stdio-and-http-transport]

key-files:
  created:
    - src/deckforge/mcp/__init__.py
    - src/deckforge/mcp/server.py
    - src/deckforge/mcp/tools.py
    - tests/test_mcp_server.py
    - .github/workflows/publish-sdk.yml
    - sdk/README.md
    - .github/ISSUE_TEMPLATE/bug_report.yml
    - .github/ISSUE_TEMPLATE/feature_request.yml
    - .github/CONTRIBUTING.md
  modified:
    - pyproject.toml
    - sdk/package.json

key-decisions:
  - "FastMCP with lazy imports in tool functions to avoid circular dependencies"
  - "MCP tool names simplified (render, generate, themes) vs internal function names for agent ergonomics"
  - "npm publish with --provenance flag for supply chain security"
  - "x402 per-call pricing: $0.05 render, $0.15 generate, free for metadata endpoints"

patterns-established:
  - "MCP tool pattern: thin wrapper functions delegating to existing service layer"
  - "Dual transport: stdio for Claude Desktop, streamable-http for production"

requirements-completed: [GTM-04, GTM-08, GTM-09, GTM-12]

# Metrics
duration: 7min
completed: 2026-03-29
---

# Phase 9 Plan 2: MCP Server + SDK Publishing + GitHub Repo Setup Summary

**FastMCP server with 6 AI-discoverable tools, GitHub Actions npm publish pipeline, 409-line marketing README with pricing/benchmarks, and open-source repo setup**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-29T18:11:37Z
- **Completed:** 2026-03-29T18:19:29Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- MCP server exposes 6 tools (render, generate, themes, slide_types, cost_estimate, pricing) with descriptive docstrings for AI agent discovery
- GitHub Actions workflow publishes @deckforge/sdk to npm on sdk-v* tag with provenance attestation
- SDK README covers quick start, 32 slide types, 24 chart types, streaming, finance examples, pricing table, and benchmarks (409 lines)
- GitHub repo has YAML form issue templates (bug report + feature request) and CONTRIBUTING.md

## Task Commits

Each task was committed atomically:

1. **Task 1: MCP server with DeckForge tools** - `2d9b374` (feat)
2. **Task 2: npm SDK publish workflow + README + GitHub repo setup** - `2366ae7` (feat)

## Files Created/Modified
- `src/deckforge/mcp/__init__.py` - Module docstring and package init
- `src/deckforge/mcp/server.py` - FastMCP server with 6 registered tools and dual transport support
- `src/deckforge/mcp/tools.py` - Tool implementations with lazy imports (render, generate, list_themes, list_slide_types, estimate_cost, get_pricing)
- `tests/test_mcp_server.py` - 22 tests covering tool registration, themes, slide types, pricing, cost estimation, render/generate with mocks
- `pyproject.toml` - Added mcp[cli]>=1.26 dependency
- `.github/workflows/publish-sdk.yml` - CI/CD for npm publish on sdk-v* tags with test job on PRs
- `sdk/README.md` - Marketing-grade docs with quick start, pricing, API reference, builder/chart factories, streaming, finance examples, benchmarks
- `sdk/package.json` - Added repository, homepage, bugs, publishConfig fields
- `.github/ISSUE_TEMPLATE/bug_report.yml` - YAML form template for bug reports
- `.github/ISSUE_TEMPLATE/feature_request.yml` - YAML form template for feature requests
- `.github/CONTRIBUTING.md` - Dev setup, testing, code style, PR process guide

## Decisions Made
- FastMCP with lazy imports in tool functions to avoid circular dependencies at module load time
- MCP tool names simplified for agent ergonomics: `render` instead of `render_presentation`, `themes` instead of `list_themes`
- npm publish uses `--provenance` flag for supply chain security (npm provenance attestation)
- x402 per-call pricing set at $0.05 for render, $0.15 for generate, free for metadata/discovery endpoints
- Default theme set to `corporate-blue` (matching actual theme YAML file names, not `corporate_navy`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Default theme corrected from corporate_navy to corporate-blue**
- **Found during:** Task 1 (MCP tools implementation)
- **Issue:** Plan referenced `corporate_navy` as default theme but no such theme exists; available themes use hyphenated names (e.g., `corporate-blue`)
- **Fix:** Used `corporate-blue` as default theme in all tool functions
- **Files modified:** src/deckforge/mcp/tools.py
- **Verification:** Theme exists in src/deckforge/themes/data/corporate-blue.yaml
- **Committed in:** 2d9b374

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Corrected an invalid theme reference. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MCP server ready for Claude Desktop integration (add to mcp config)
- SDK ready for npm publish once NPM_TOKEN secret is added to GitHub repo settings
- GitHub repo has professional open-source presence with issue templates and contribution guide

## Self-Check: PASSED

All 9 created files verified on disk. Both task commits (2d9b374, 2366ae7) verified in git log.

---
*Phase: 09-monetization-and-go-to-market*
*Completed: 2026-03-29*
