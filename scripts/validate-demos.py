#!/usr/bin/env python3
"""Validate all 5 demo deck IRs render to valid .pptx files.

Loads each demo IR from demos/*/ir.json, validates against the Pydantic
IR schema, renders via the render pipeline, and verifies the output.

Can run in two modes:
  1. API mode (default): POSTs to running API server
  2. Direct mode (--direct): Imports renderer directly (no server needed)

Usage:
  python scripts/validate-demos.py                     # API mode
  python scripts/validate-demos.py --direct             # Direct render
  python scripts/validate-demos.py --api-key dk_test_   # Custom key

Requirements (direct mode):
  pip install -e .   (or ensure src/ is on PYTHONPATH)

Requirements (API mode):
  Running API server + valid API key
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMOS_DIR = PROJECT_ROOT / "demos"
OUTPUT_DIR = PROJECT_ROOT / "tmp" / "demo-validation"

EXPECTED_DEMOS = [
    "mckinsey-strategy",
    "pe-deal-memo",
    "startup-pitch",
    "board-update",
    "product-launch",
]


def validate_pptx(filepath: Path) -> tuple[bool, str]:
    """Check file is valid PPTX (ZIP with PK header, >5KB)."""
    if not filepath.exists():
        return False, "File does not exist"
    size = filepath.stat().st_size
    if size < 5000:
        return False, f"Too small: {size} bytes (expected >5000)"
    with open(filepath, "rb") as f:
        header = f.read(2)
    if header != b"PK":
        return False, f"Invalid header: {header!r} (expected b'PK')"
    return True, f"Valid PPTX ({size:,} bytes)"


def validate_ir_schema(ir_path: Path) -> tuple[bool, str]:
    """Validate IR JSON against the Pydantic Presentation model."""
    try:
        # Add project root to sys.path so deckforge is importable
        if str(PROJECT_ROOT / "src") not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT / "src"))
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        from deckforge.ir import Presentation

        with open(ir_path) as f:
            data = json.load(f)
        Presentation.model_validate(data)
        return True, "Schema valid"
    except Exception as e:
        return False, f"Schema error: {e}"


def render_via_api(
    ir_data: dict, output_path: Path, api_url: str, api_key: str
) -> tuple[bool, str]:
    """Render IR via POST to /v1/render.

    The render endpoint accepts a Presentation object directly as the body
    (not wrapped in {"presentation": ...}).
    """
    import urllib.error
    import urllib.request

    body = json.dumps(ir_data).encode("utf-8")
    req = urllib.request.Request(
        f"{api_url}/v1/render",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.read())
            return True, f"Rendered -> {output_path.name}"
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")[:300]
        return False, f"HTTP {e.code}: {body_text}"
    except Exception as e:
        return False, f"Error: {e}"


def render_direct(ir_data: dict, output_path: Path) -> tuple[bool, str]:
    """Render IR directly using the render_pipeline (no server needed).

    Uses the same render_pipeline function that the API and workers use.
    Returns (pptx_bytes, QAReport) per decision [07-03].
    """
    try:
        # Ensure src/ is on path
        if str(PROJECT_ROOT / "src") not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT / "src"))
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        from deckforge.ir import Presentation
        from deckforge.workers.tasks import render_pipeline

        presentation = Presentation.model_validate(ir_data)
        pptx_bytes, qa_report = render_pipeline(presentation)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pptx_bytes)

        return True, f"Rendered -> {output_path.name} (QA score: {qa_report.score})"
    except Exception as e:
        return False, f"Render error: {e}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate all 5 demo deck IRs render to valid .pptx files"
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Use direct Python render (no API server needed)",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("DECKFORGE_API_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("DECKFORGE_TEST_API_KEY", ""),
        help="API key for authentication",
    )
    parser.add_argument(
        "--demo",
        choices=EXPECTED_DEMOS,
        help="Validate a single demo instead of all 5",
    )
    args = parser.parse_args()

    print("=== DeckForge Demo Deck Validation ===")
    print(f"  Mode:  {'Direct render' if args.direct else 'API (' + args.api_url + ')'}")
    print(f"  Demos: {DEMOS_DIR}")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    demos_to_validate = [args.demo] if args.demo else EXPECTED_DEMOS
    passed = 0
    failed = 0
    skipped = 0
    start_time = time.time()

    for demo_name in demos_to_validate:
        ir_path = DEMOS_DIR / demo_name / "ir.json"
        output_path = OUTPUT_DIR / f"{demo_name}.pptx"

        print(f"--- {demo_name} ---")

        # Check IR file exists
        if not ir_path.exists():
            print(f"  FAIL: {ir_path} not found")
            failed += 1
            print()
            continue

        # Load IR JSON
        with open(ir_path) as f:
            ir_data = json.load(f)
        slide_count = len(ir_data.get("slides", []))
        print(f"  Loaded: {slide_count} slides")

        # Validate against Pydantic schema
        ok, msg = validate_ir_schema(ir_path)
        print(f"  Schema: {msg}")
        if not ok:
            failed += 1
            print()
            continue

        # Render
        if args.direct:
            ok, msg = render_direct(ir_data, output_path)
        else:
            if not args.api_key:
                print("  SKIP: No API key (set DECKFORGE_TEST_API_KEY or use --direct)")
                skipped += 1
                print()
                continue
            ok, msg = render_via_api(ir_data, output_path, args.api_url, args.api_key)

        print(f"  Render: {msg}")
        if not ok:
            failed += 1
            print()
            continue

        # Validate output PPTX
        ok, msg = validate_pptx(output_path)
        print(f"  Output: {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

        print()

    elapsed = time.time() - start_time
    total = len(demos_to_validate)
    print("=== Results ===")
    print(f"  Total:   {total}")
    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Time:    {elapsed:.1f}s")
    print()

    if failed > 0:
        print(f"FAILED: {failed}/{total} demos failed validation")
        sys.exit(1)
    elif skipped == total:
        print("SKIPPED: All demos skipped (no API key and --direct not used)")
        print("  Try: python scripts/validate-demos.py --direct")
        sys.exit(0)
    else:
        print(f"PASSED: {passed}/{total} demos validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
