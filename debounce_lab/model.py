"""Validated trace data shared by the simulator and its presentation layers."""

from dataclasses import dataclass
from typing import Any

MAX_DURATION_MS = 86_400_000
MAX_EDGES = 10_000


def integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be an integer between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class Edge:
    at_ms: int
    level: int


@dataclass(frozen=True)
class Trace:
    name: str
    duration_ms: int
    initial_level: int
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not 1 <= len(self.name) <= 200:
            raise ValueError("name must be a nonempty string of at most 200 characters")
        if any(ord(char) < 32 or ord(char) == 127 for char in self.name):
            raise ValueError("name must not contain control characters")
        integer(self.duration_ms, "duration_ms", 1, MAX_DURATION_MS)
        integer(self.initial_level, "initial_level", 0, 1)
        if not isinstance(self.edges, tuple) or len(self.edges) > MAX_EDGES:
            raise ValueError(f"edges must be a tuple of at most {MAX_EDGES} transitions")
        previous_time, previous_level = -1, self.initial_level
        for edge in self.edges:
            if not isinstance(edge, Edge):
                raise ValueError("each transition must be an Edge")
            integer(edge.at_ms, "at_ms", 0, self.duration_ms)
            integer(edge.level, "level", 0, 1)
            if edge.at_ms <= previous_time:
                raise ValueError("edge timestamps must be strictly increasing")
            if edge.level == previous_level:
                raise ValueError("each edge must change the preceding level")
            previous_time, previous_level = edge.at_ms, edge.level

    @classmethod
    def from_dict(cls, data: Any) -> "Trace":
        expected = {"name", "duration_ms", "initial_level", "edges"}
        if not isinstance(data, dict) or set(data) != expected:
            raise ValueError("trace requires exactly: name, duration_ms, initial_level, edges")
        raw_edges = data["edges"]
        if not isinstance(raw_edges, list) or len(raw_edges) > MAX_EDGES:
            raise ValueError(f"edges must be a list of at most {MAX_EDGES} transitions")
        edges = []
        for item in raw_edges:
            if not isinstance(item, dict) or set(item) != {"at_ms", "level"}:
                raise ValueError("each edge requires exactly: at_ms, level")
            edges.append(Edge(item["at_ms"], item["level"]))
        return cls(data["name"], data["duration_ms"], data["initial_level"], tuple(edges))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            "initial_level": self.initial_level,
            "edges": [edge_dict(edge) for edge in self.edges],
        }


def edge_dict(edge: Edge) -> dict:
    return {"at_ms": edge.at_ms, "level": edge.level}
