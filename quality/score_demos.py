"""Score the 5 bundled demo decks with the PPTEval-style harness.

Usage::

    python -m quality.score_demos                 # human-readable table
    python -m quality.score_demos --json report.json
    python -m quality.score_demos --markdown report.md

Run from the repo root.  Requires only the project package on the path
(``pip install -e .`` or ``PYTHONPATH=src``); no Postgres/Redis/LLM keys.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The 5 demo decks the repo renders end to end.
DEMO_NAMES = [
    "mckinsey-strategy",
    "pe-deal-memo",
    "startup-pitch",
    "board-update",
    "product-launch",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMOS_DIR = REPO_ROOT / "demos"


def _ensure_src_on_path() -> None:
    src = REPO_ROOT / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def score_all() -> list[dict]:
    _ensure_src_on_path()
    from quality.ppteval import load_demo, score_presentation

    results: list[dict] = []
    for name in DEMO_NAMES:
        demo_dir = DEMOS_DIR / name
        if not (demo_dir / "ir.json").exists():
            results.append({"name": name, "error": "ir.json not found"})
            continue
        presentation = load_demo(demo_dir)
        results.append(score_presentation(presentation, name=name).to_dict())
    return results


def _render_table(results: list[dict]) -> str:
    lines = [
        "PPTEval-style demo deck scores (1-5 scale)",
        "=" * 72,
        f"{'deck':<20}{'slides':>7}{'content':>9}{'design':>8}{'coher.':>8}{'overall':>9}",
        "-" * 72,
    ]
    scored = [r for r in results if "error" not in r]
    for r in results:
        if "error" in r:
            lines.append(f"{r['name']:<20}  ERROR: {r['error']}")
            continue
        d = r["dimensions"]
        lines.append(
            f"{r['name']:<20}{r['slide_count']:>7}"
            f"{d['content']['score']:>9.2f}{d['design']['score']:>8.2f}"
            f"{d['coherence']['score']:>8.2f}{r['overall']:>9.2f}"
        )
    lines.append("-" * 72)
    if scored:
        mean_overall = sum(r["overall"] for r in scored) / len(scored)
        lines.append(f"{'MEAN':<20}{'':>7}{'':>9}{'':>8}{'':>8}{mean_overall:>9.2f}")
    return "\n".join(lines)


def _render_markdown(results: list[dict]) -> str:
    lines = [
        "# DeckForge demo-deck quality report",
        "",
        "PPTEval-style scoring (Content / Design / Coherence, each 1-5).",
        "Heuristic regression guard, not a learned judge -- see "
        "`quality/ppteval.py`.",
        "",
        "| Deck | Slides | Content | Design | Coherence | Overall |",
        "|------|-------:|--------:|-------:|----------:|--------:|",
    ]
    scored = [r for r in results if "error" not in r]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['name']} | - | - | - | - | ERROR: {r['error']} |")
            continue
        d = r["dimensions"]
        lines.append(
            f"| {r['name']} | {r['slide_count']} "
            f"| {d['content']['score']:.2f} | {d['design']['score']:.2f} "
            f"| {d['coherence']['score']:.2f} | {r['overall']:.2f} |"
        )
    if scored:
        mean_overall = sum(r["overall"] for r in scored) / len(scored)
        lines.append(f"| **mean** | | | | | **{mean_overall:.2f}** |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score the demo decks (PPTEval-style).")
    parser.add_argument("--json", metavar="PATH", help="write the full JSON report here")
    parser.add_argument("--markdown", metavar="PATH", help="write a Markdown report here")
    args = parser.parse_args(argv)

    results = score_all()

    if args.json:
        Path(args.json).write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        print(f"wrote JSON report -> {args.json}")
    if args.markdown:
        Path(args.markdown).write_text(_render_markdown(results), encoding="utf-8")
        print(f"wrote Markdown report -> {args.markdown}")

    print(_render_table(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
