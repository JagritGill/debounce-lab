# Debounce Lab

**Turn a noisy button trace into an explainable debounce experiment.**

A small, offline Python CLI compares a quiet-window debouncer with an immediate
edge-lockout debouncer. It produces exact event times, machine-readable JSON,
and a self-contained HTML signal report. No hardware, network, package install,
or API key is needed.

## Quickstart

Use Python 3.11 or newer. From this folder:

```sh
python3 -m debounce_lab examples/bouncy-button.json
python3 -m debounce_lab examples/short-tap.json --format json
mkdir -p out
python3 -m debounce_lab examples/bouncy-button.json --format html --output out/button.html
python3 -m debounce_lab examples/short-tap.json --format html --output out/short-tap.html
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
```

Open `out/button.html` or `out/short-tap.html` in a browser (on macOS,
`open out/button.html`). Reports contain inline SVG and CSS; no server or
JavaScript is required. Output files must not already exist. Choose a new
filename when repeating a command. Omit `--output` to write to stdout.

Expected output for the first command:

```text
A bouncy press and release | 160 ms | window 12 ms
raw: 8 transitions; initial level 0
stable: [32:1, 118:0] | presses=1 releases=1 final=0
lockout: [10:1, 100:0] | presses=1 releases=1 final=0
```

`32:1` means the output became pressed at 32 ms. With the short-tap example,
stable emits no events, while lockout emits a press at 10 ms and misses the
release at 15 ms. Its final state remains pressed. This is an intentional
counterexample showing why algorithm choice matters, not a claim that stable
debouncing always matches human intent.

## Supply your own trace

```json
{
  "name": "One clean press",
  "duration_ms": 100,
  "initial_level": 0,
  "edges": [{"at_ms": 10, "level": 1}]
}
```

Each edge is a transition, not a repeated sample. Timestamps must strictly
increase and fall within the trace. Levels must alternate between integer 0
and 1. The initial level is assumed stable. An empty edge list is valid.
The schema rejects extra fields, duplicate JSON keys, booleans in integer
fields, and control characters in the name. Limits: a 200-character name,
10,000 edges, 2 MB input, and a 24-hour horizon. Files are treated as data only.

```sh
python3 -m debounce_lab examples/threshold-tie.json --window-ms 12
python3 -m debounce_lab --help
```

The stable method gives input edges priority over simultaneous timer expiry.
A pulse exactly as wide as the window is therefore suppressed. Window values
are positive integer milliseconds. Exit status is 0 on success and 2 on
validation or file errors.

## How it works

| Method | State | Emits output when | Main tradeoff |
| --- | --- | --- | --- |
| Stable | raw level, output level, pending deadline | Input remains changed through a quiet window | Delays response; short pulses disappear |
| Lockout | output level, next eligible time | An eligible edge differs from output | Immediate response; ignored edges can leave stale state |

See [architecture and interview notes](docs/architecture.md) for timer ordering,
complexity, module boundaries, and extension ideas. Tests include boundary
cases, input errors, safe output handling, report escaping, determinism, and
2,048 exhaustive short-trace comparisons to a separate tick-based oracle.

## Honest scope

Examples are synthetic; counts describe output transitions, not verified human
presses. This is a digital educational model with 1 ms resolution, not measured
hardware, a circuit simulator, or production firmware. There are no adoption
or performance claims. Generated reports can become large for large traces.

Created with AI assistance; see [dependency attribution and provenance](THIRD_PARTY_NOTICES.md).
Original project files are available under the [MIT License](LICENSE).
