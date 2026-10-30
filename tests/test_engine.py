import itertools
import json
from pathlib import Path
import unittest

from debounce_lab.engine import compare, simulate
from debounce_lab.model import Edge, Trace

ROOT = Path(__file__).resolve().parents[1]


def reference_stable(trace, window):
    """Independent integer-tick oracle, intentionally slow and easy to inspect."""
    inputs = {edge.at_ms: edge.level for edge in trace.edges}
    raw = output = trace.initial_level
    changed_at = None
    result = []
    for tick in range(trace.duration_ms + 1):
        if tick in inputs:
            raw = inputs[tick]
            changed_at = tick
        if raw != output and changed_at is not None and tick - changed_at >= window:
            output = raw
            result.append(Edge(tick, output))
    return tuple(result)


class EngineTests(unittest.TestCase):
    def trace(self, edges, duration=100, initial=0):
        return Trace("test", duration, initial, tuple(Edge(*edge) for edge in edges))

    def test_bouncy_button_example(self):
        trace = Trace.from_dict(json.loads((ROOT / "examples/bouncy-button.json").read_text()))
        stable, lockout = compare(trace, 12)
        self.assertEqual(stable.events, (Edge(32, 1), Edge(118, 0)))
        self.assertEqual(lockout.events, (Edge(10, 1), Edge(100, 0)))

    def test_short_tap_exposes_stuck_lockout(self):
        trace = self.trace([(10, 1), (15, 0)])
        stable, lockout = compare(trace, 12)
        self.assertEqual(stable.events, ())
        self.assertEqual(lockout.events, (Edge(10, 1),))
        self.assertEqual(lockout.to_dict(0)["final_level"], 1)

    def test_exact_threshold_edge_cancels_confirmation(self):
        self.assertEqual(simulate(self.trace([(10, 1), (22, 0)]), 12).events, ())

    def test_pulse_one_ms_over_threshold_survives(self):
        self.assertEqual(simulate(self.trace([(10, 1), (23, 0)]), 12).events,
                         (Edge(22, 1), Edge(35, 0)))

    def test_horizon_is_inclusive(self):
        self.assertEqual(simulate(self.trace([(10, 1)], duration=22), 12).events, (Edge(22, 1),))
        self.assertEqual(simulate(self.trace([(10, 1)], duration=21), 12).events, ())

    def test_initial_pressed_state(self):
        trace = self.trace([(0, 0)], initial=1)
        self.assertEqual(simulate(trace, 12).events, (Edge(12, 0),))
        self.assertEqual(simulate(trace, 12, "lockout").events, (Edge(0, 0),))

    def test_empty_trace_preserves_initial_state(self):
        for initial in (0, 1):
            for result in compare(self.trace([], initial=initial), 12):
                self.assertEqual(result.events, ())
                self.assertEqual(result.to_dict(initial)["final_level"], initial)

    def test_lockout_accepts_at_exact_unlock(self):
        trace = self.trace([(10, 1), (22, 0)])
        self.assertEqual(simulate(trace, 12, "lockout").events, trace.edges)

    def test_invalid_algorithm_and_windows(self):
        trace = self.trace([])
        for window in (0, -1, True, 0.5, 86_400_001):
            with self.subTest(window=window), self.assertRaises(ValueError):
                simulate(trace, window)
        with self.assertRaises(ValueError):
            simulate(trace, 12, "magic")

    def test_exhaustive_short_traces_against_tick_oracle(self):
        cases = 0
        for initial, mask, window in itertools.product((0, 1), range(256), range(1, 5)):
            level, edges = initial, []
            for tick in range(8):
                if mask & (1 << tick):
                    level = 1 - level
                    edges.append(Edge(tick, level))
            trace = Trace("exhaustive", 12, initial, tuple(edges))
            with self.subTest(initial=initial, mask=mask, window=window):
                stable, lockout = compare(trace, window)
                self.assertEqual(stable.events, reference_stable(trace, window))
                for result in (stable, lockout):
                    self.assertTrue(all(0 <= event.at_ms <= trace.duration_ms for event in result.events))
                    levels = [trace.initial_level] + [event.level for event in result.events]
                    self.assertTrue(all(a != b for a, b in zip(levels, levels[1:])))
                    self.assertTrue(all(b.at_ms - a.at_ms >= window for a, b in
                                        zip(result.events, result.events[1:])))
                self.assertEqual(stable.to_dict(initial)["final_level"], level)
                self.assertTrue(all(event in trace.edges for event in lockout.events))
            cases += 1
        self.assertEqual(cases, 2048)
