"""Command-line entry point: python3 -m debounce_lab."""

import argparse
import json
from pathlib import Path
import sys

from .engine import compare
from .model import Trace
from .report import render_html

MAX_INPUT_BYTES = 2_000_000


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two digital switch debouncers, entirely offline.")
    parser.add_argument("trace", type=Path, help="JSON trace file")
    parser.add_argument("--window-ms", type=int, default=12, help="positive integer debounce window (default: 12)")
    parser.add_argument("--format", choices=("text", "json", "html"), default="text")
    parser.add_argument("--output", type=Path, help="write a new file; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        with args.trace.open("rb") as handle:
            payload = handle.read(MAX_INPUT_BYTES + 1)
        if len(payload) > MAX_INPUT_BYTES:
            raise ValueError(f"trace exceeds {MAX_INPUT_BYTES} bytes")
        trace = Trace.from_dict(json.loads(payload, object_pairs_hook=_unique_object))
        results = compare(trace, args.window_ms)
        if args.format == "json":
            rendered = json.dumps({"trace": trace.to_dict(), "results": [
                result.to_dict(trace.initial_level) for result in results]}, indent=2) + "\n"
        elif args.format == "html":
            rendered = render_html(trace, results)
        else:
            lines = [f"{trace.name} | {trace.duration_ms} ms | window {args.window_ms} ms",
                     f"raw: {len(trace.edges)} transitions; initial level {trace.initial_level}"]
            for result in results:
                data = result.to_dict(trace.initial_level)
                events = ", ".join(f"{edge.at_ms}:{edge.level}" for edge in result.events) or "(none)"
                lines.append(f"{result.algorithm}: [{events}] | presses={data['presses']} "
                             f"releases={data['releases']} final={data['final_level']}")
            rendered = "\n".join(lines) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            sys.stdout.write(rendered)
    except (OSError, ValueError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
