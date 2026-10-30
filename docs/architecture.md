# Architecture and interview notes

```text
JSON file -> strict Trace model -> pure simulation -> Result records
                                                     |-- text
                                                     |-- JSON
                                                     `-- HTML + inline SVG
```

`model.py` owns immutable records and input invariants. `engine.py` contains the
state machines. `report.py` formats results and escapes untrusted trace names.
`__main__.py` handles file I/O, argument parsing, and error messages. Neither
the model nor simulator reads files, uses a wall clock, or sleeps.

## Precise model

- Time is integer milliseconds in the closed interval `[0, duration_ms]`.
- `initial_level` is already stable immediately before time zero. An edge at
  zero is allowed. Every edge changes the input; duplicate timestamps or levels
  are rejected rather than silently sorted or normalized.
- The horizon is inclusive. A timer due at the horizon fires unless an input
  edge at that same instant cancels it. A future timer beyond the horizon is
  not emitted.
- For stable debouncing, input edges win ties with timers. A pulse whose width
  equals the debounce window is suppressed. A pulse one millisecond wider can
  produce an output press and a later release.
- Lockout accepts an eligible input transition immediately. It accepts another
  at or after `accepted_time + window_ms`. Ignored edges are discarded, and no
  timer rechecks the input at expiry. That deliberately simple strategy can
  get stuck after a short pulse; the example documents this behavior.

## Decisions and tradeoffs

The simulator iterates over transitions, not every millisecond. Each input edge
requires constant work and there is at most one pending timer: simulation is
O(E) time and O(E) output memory for E edges. This is an algorithmic bound, not
a measured performance claim. A deliberately different integer-tick reference
implementation in the tests checks all 2,048 combinations of initial state,
short edge sequence, and selected windows.

The stable method trades response time for a quiet-window requirement. The
lockout method trades immediate response for lost transitions. Neither can
infer user intent from a signal alone. Adding a minimum press duration or
ground-truth annotations would be a separate policy layer.

Integer time avoids floating-point boundary ambiguity. The tradeoff is 1 ms
resolution. Immutable input makes repeatability and testing straightforward.
The standalone report avoids a JS toolchain or web service; changing the
window requires rerunning the CLI. Full raw and output tables supplement the
chart for accessibility. Large traces can yield a large report despite the
input caps; CLI text or JSON is preferable for those cases.

## Extensions worth discussing

1. A sampled integrator algorithm with an explicit sampling period, compared
   against these event-driven methods.
2. Hardware trace import with a declared timestamp precision and polarity.
3. Ground-truth press annotations for measuring false positives and latency.
4. Streaming operation that preserves a pending timer across chunks.

## Limitations

No GPIO access, analog voltages, metastability, RC circuits, interrupt timing,
timer rollover, multi-key interactions, or electrical safety analysis are
modeled. Active-high is the display convention. This is a teaching and
exploration tool, not a validated firmware component or circuit simulator.
