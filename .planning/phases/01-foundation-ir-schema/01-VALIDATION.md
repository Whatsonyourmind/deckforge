---
phase: 1
slug: foundation-ir-schema
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x with pytest-asyncio |
| **Config file** | pyproject.toml (pytest section) |
| **Quick run command** | `python -m pytest tests/unit -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | IR-01 | unit | `pytest tests/unit/test_ir_slides.py` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | IR-02 | unit | `pytest tests/unit/test_ir_elements.py` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | IR-03 | unit | `pytest tests/unit/test_ir_charts.py` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | IR-04 | unit | `pytest tests/unit/test_ir_validation.py` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | IR-05, IR-06 | unit | `pytest tests/unit/test_ir_metadata.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | INFRA-01 | integration | `docker compose up -d && pytest tests/integration/test_docker.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | INFRA-02 | unit | `pytest tests/unit/test_fonts.py` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | INFRA-03 | integration | `pytest tests/integration/test_db.py` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | INFRA-04 | integration | `alembic upgrade head` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | API-08 | integration | `pytest tests/integration/test_health.py` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | API-09 | integration | `pytest tests/integration/test_auth.py` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 2 | API-10 | integration | `pytest tests/integration/test_rate_limit.py` | ❌ W0 | ⬜ pending |
| 01-03-04 | 03 | 2 | API-11 | integration | `pytest tests/integration/test_openapi.py` | ❌ W0 | ⬜ pending |
| 01-03-05 | 03 | 2 | API-14 | integration | `pytest tests/integration/test_idempotency.py` | ❌ W0 | ⬜ pending |
| 01-03-06 | 03 | 2 | WORKER-01..05 | integration | `pytest tests/integration/test_workers.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (db session, redis, api client)
- [ ] `tests/unit/` — directory structure for unit tests
- [ ] `tests/integration/` — directory structure for integration tests
- [ ] pytest + pytest-asyncio + httpx installed in pyproject.toml

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker Compose full stack | INFRA-01 | Requires Docker daemon | Run `docker compose up -d`, verify all services healthy |
| OpenAPI at /docs | API-11 | Visual verification | Open http://localhost:8000/docs, verify IR models visible |
| MinIO file upload | WORKER-03 | Requires running MinIO | Upload test file via boto3, verify retrieval |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
