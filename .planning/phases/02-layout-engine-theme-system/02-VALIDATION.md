---
phase: 2
slug: layout-engine-theme-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x with pytest-asyncio |
| **Config file** | pyproject.toml (pytest section) |
| **Quick run command** | `python -m pytest tests/unit/test_layout*.py tests/unit/test_theme*.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | LAYOUT-01, LAYOUT-06 | unit | `pytest tests/unit/test_layout_solver.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | LAYOUT-02 | unit | `pytest tests/unit/test_text_measure.py` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | LAYOUT-03, LAYOUT-04, LAYOUT-05 | unit | `pytest tests/unit/test_layout_adaptive.py` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | THEME-01, THEME-02 | unit | `pytest tests/unit/test_theme_registry.py` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | THEME-03 | unit | `pytest tests/unit/test_brand_kit.py` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | THEME-04, THEME-05 | unit | `pytest tests/unit/test_theme_colors.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_layout_solver.py` — stubs for constraint solver
- [ ] `tests/unit/test_text_measure.py` — stubs for text measurement
- [ ] `tests/unit/test_theme_registry.py` — stubs for theme loading

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual layout quality | LAYOUT-01 | Aesthetic judgment | Generate test slides, visually inspect in PowerPoint |
| Theme visual distinction | THEME-01 | Aesthetic judgment | Apply 3 different themes to same IR, compare screenshots |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
