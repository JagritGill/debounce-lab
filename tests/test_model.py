import unittest

from debounce_lab.model import Edge, Trace


class ModelTests(unittest.TestCase):
    def valid(self):
        return {"name": "button", "duration_ms": 20, "initial_level": 0,
                "edges": [{"at_ms": 1, "level": 1}, {"at_ms": 5, "level": 0}]}

    def test_round_trip(self):
        self.assertEqual(Trace.from_dict(self.valid()).to_dict(), self.valid())

    def test_rejects_bad_schema(self):
        for bad in ([], {}, {**self.valid(), "surprise": 1}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Trace.from_dict(bad)

    def test_rejects_invalid_fields(self):
        invalid = {
            "name": [None, "", "x" * 201, "bad\x1b[31m", "bad\nname"],
            "duration_ms": [0, -1, True, 3.5, 86_400_001],
            "initial_level": [False, -1, 2, 0.0],
            "edges": [None, {}, [{"at_ms": 2}], [{"at_ms": 2, "level": 1, "extra": 0}]],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    Trace.from_dict({**self.valid(), field: value})

    def test_rejects_invalid_edges(self):
        variants = [
            [Edge(5, 1), Edge(2, 0)], [Edge(2, 1), Edge(2, 0)],
            [Edge(-1, 1)], [Edge(21, 1)], [Edge(1, 0)],
            [Edge(1, True)], [Edge(1.1, 1)], [Edge(True, 1)],
        ]
        for edges in variants:
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                Trace("bad", 20, 0, tuple(edges))

    def test_rejects_excess_edges(self):
        with self.assertRaises(ValueError):
            Trace.from_dict({**self.valid(), "edges": [{}] * 10_001})

    def test_trace_is_immutable(self):
        trace = Trace.from_dict(self.valid())
        with self.assertRaises(AttributeError):
            trace.duration_ms = 10
