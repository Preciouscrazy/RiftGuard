"""Command-line JSON analysis and optional portable HTML dashboard."""
import argparse
import json
from pathlib import Path
import sys
from .analyzer import analyze_events
from .dashboard import save_dashboard


def main():
    parser = argparse.ArgumentParser(description="Analyze event logs and build a dashboard")
    parser.add_argument("input", help="Input JSON event array")
    parser.add_argument("--output", help="Optional JSON output path; stdout if omitted")
    parser.add_argument("--dashboard", help="Optional offline HTML dashboard path")
    args = parser.parse_args()
    try:
        targets = [v for v in (args.output, args.dashboard) if v]
        if any(Path(p).resolve() == Path(args.input).resolve() for p in targets):
            raise ValueError("Output must not overwrite input")
        if len(targets) == 2 and Path(targets[0]).resolve() == Path(targets[1]).resolve():
            raise ValueError("JSON report and dashboard must have different paths")
        events = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        report = analyze_events(events)
        if args.dashboard:
            save_dashboard(events, args.dashboard)
        if args.output:
            Path(args.output).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            print(f"Saved {args.output}")
        else:
            print(json.dumps(report, indent=2, allow_nan=False))
        if args.dashboard:
            print(f"Saved {args.dashboard}", file=sys.stderr)
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
