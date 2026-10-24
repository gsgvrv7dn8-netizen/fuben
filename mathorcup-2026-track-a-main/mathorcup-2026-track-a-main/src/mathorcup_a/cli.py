"""AI-assisted CLI for local, exploratory standardized-target evaluation."""

import argparse
import json
from pathlib import Path
import sys

from .tracking import PROJECT_ROOT, run_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True, type=Path, help="Attachment 1.csv")
    parser.add_argument("--targets", required=True, type=Path, help="Attachment 4.csv")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs/exploratory_v0.json")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "runs")
    parser.add_argument("--run-id", help="Optional unique safe ID; existing runs are never overwritten")
    args = parser.parse_args(argv)
    try:
        output = run_experiment(args.features, args.targets, args.config, args.output_root, args.run_id)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "completed", "output": str(output),
                      "summary": str(output / "summary.json"),
                      "official_final_output": False}, ensure_ascii=False))
    return 0
