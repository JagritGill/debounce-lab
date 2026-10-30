"""Pure event-driven debouncers; no sleeping, clocks, I/O, or randomness."""

from dataclasses import dataclass

from .model import Edge, MAX_DURATION_MS, Trace, edge_dict, integer


@dataclass(frozen=True)
class Result:
    algorithm: str
    window_ms: int
    events: tuple[Edge, ...]

    def to_dict(self, initial_level: int) -> dict:
        return {
            "algorithm": self.algorithm,
            "window_ms": self.window_ms,
            "events": [edge_dict(edge) for edge in self.events],
            "presses": sum(edge.level == 1 for edge in self.events),
            "releases": sum(edge.level == 0 for edge in self.events),
            "final_level": self.events[-1].level if self.events else initial_level,
        }


def simulate(trace: Trace, window_ms: int, algorithm: str = "stable") -> Result:
    """Debounce a trace, including pending confirmations through its horizon.

    Stable: confirm a changed input after a quiet window. An input edge at the
    exact confirmation time wins the tie and can cancel that confirmation.
    Lockout: accept an edge immediately, then ignore edges during the window.
    Ignored edges are not replayed after lockout expires.
    """
    integer(window_ms, "window_ms", 1, MAX_DURATION_MS)
    if algorithm not in {"stable", "lockout"}:
        raise ValueError("algorithm must be stable or lockout")
    output = raw = trace.initial_level
    events: list[Edge] = []
    deadline: int | None = None
    unlock_at = 0
    for edge in trace.edges:
        if algorithm == "stable":
            if deadline is not None and deadline < edge.at_ms:
                output = raw
                events.append(Edge(deadline, output))
            raw = edge.level
            deadline = edge.at_ms + window_ms if raw != output else None
        elif edge.at_ms >= unlock_at and edge.level != output:
            output = edge.level
            events.append(edge)
            unlock_at = edge.at_ms + window_ms
    if algorithm == "stable" and deadline is not None and deadline <= trace.duration_ms:
        events.append(Edge(deadline, raw))
    return Result(algorithm, window_ms, tuple(events))


def compare(trace: Trace, window_ms: int) -> tuple[Result, Result]:
    return simulate(trace, window_ms, "stable"), simulate(trace, window_ms, "lockout")
