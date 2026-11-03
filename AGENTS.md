# Working in Debounce Lab

Offline Python simulator for comparing digital switch debounce policies.
Read [README](README.md) for the input contract and
[architecture](docs/architecture.md) for event ordering and tradeoffs.
Original files use [MIT](LICENSE); retain [provenance](THIRD_PARTY_NOTICES.md)
and the distinction between synthetic examples and measured hardware.

## Map and invariants

| Location | Responsibility |
| --- | --- |
| `debounce_lab/model.py` | Immutable Trace/Edge records and validation |
| `debounce_lab/engine.py` | Pure stable/lockout simulation and result records |
| `debounce_lab/report.py` | Escaped, self-contained HTML/SVG report |
| `debounce_lab/__main__.py` | Bounded input, CLI options, formatting, file I/O |
| `tests/` | Models, CLI, independent tick-reference tests, release-pattern checks |
| `examples/`, `scripts/check_release.py` | Synthetic traces and release inventory/scanning |

- Time is integer milliseconds; input edges are strictly increasing, alternate
  levels, and lie in the inclusive trace horizon. Booleans are not integers here.
- Stable: an input edge wins a tie with confirmation. A pulse exactly as long
  as the window is suppressed; a confirmation at the horizon can fire.
- Lockout: accept eligible edges immediately; ignored edges are never replayed.
  A missed release can intentionally leave stale output. Do not silently turn
  this teaching counterexample into another algorithm.
- Keep the engine independent of clocks, sleep, I/O, randomness, and hardware.
  Work at event boundaries, not every millisecond in production.
- Exercise malformed Unicode and valid emoji when changing name handling. JSON
  acceptance alone does not guarantee UTF-8 output can encode a name; verify
  failure effects before opening files. Keep escaping and script-free reports.
- Output files must be new. Exclusive creation prevents overwriting; ordinary
  write failures can leave a partial new file. Do not claim atomic publication.

## Setup and verified commands

Run from this repository root with Python 3.11+. Standard library only; no
install, build, environment file, or service is required.

```sh
python3 --version
python3 -m debounce_lab examples/bouncy-button.json
python3 -m debounce_lab examples/short-tap.json --format json
python3 -m debounce_lab examples/threshold-tie.json --window-ms 12
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
git diff --check
```

These examples should exit 0. The bouncy trace gives stable `32:1, 118:0` and
lockout `10:1, 100:0`. Invalid input/file errors exit 2. See the README to save
HTML; choose a fresh filename under ignored `out/` on each run.
No static Python checker is configured; do not describe runtime tests as one.

For behavior changes, reproduce the defect and add a regression that fails
before the fix. Retain independent tick-reference coverage and exhaustive traces.
For lockout changes, check exact event sequences as well as general invariants.
Include boundary ties, horizon behavior, validation, and output effects relevant
to the change. Rendering changes need escaping/content checks and local visual
inspection. For documentation-only edits, verify commands/links and the release
check; do not invent tests that merely repeat the implementation.

## Ownership and handoff

Before editing, run `git status --short --branch` and `git diff --stat`. Preserve
pre-existing changes; never reset, clean, or stage unrelated work. This repo's
origin is `JagritGill/debounce-lab`. In the managed portfolio workspace, consult
the parent `PROJECTS.md` and `BUILD_STATUS.md` if present and coordinate with the
current task owner before overlapping work. Use the connected Mac for Jagrit's
portfolio tasks; report disconnection instead of switching executors.

Use only this original project and synthetic fixtures; do not read/copy private
or employer source or include credentials/personal paths. Keep generated output
in `out/`. Register intentionally added files in the release inventory and keep
them scanned; passing the heuristic scan alone does not establish safe provenance.
Do not use CodeRabbit or send it code. Use local review/tests and existing CI.

Follow the current request's scope: local edits do not authorize commits, pushes,
merges, releases, account/security changes, paid services, or hardware actions.
Do not bypass failing checks. Handoff should list changed files, exact commands
and exits, environment, remaining limits, and local/published state. Distinguish
checks run now from older CI evidence; never imply unobserved CI success.
