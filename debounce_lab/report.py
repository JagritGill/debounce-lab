"""Self-contained, script-free HTML/SVG reports."""

from html import escape

from .engine import Result
from .model import Edge, Trace


def _path(edges: tuple[Edge, ...], initial: int, duration: int, row: int) -> str:
    def x(at: int) -> float:
        return 150 + 790 * at / duration

    def y(level: int) -> int:
        return 65 + row * 110 + (1 - level) * 40

    level = initial
    parts = [f"M 150 {y(level)}"]
    for edge in edges:
        parts.append(f"H {x(edge.at_ms):.3f} V {y(edge.level)}")
        level = edge.level
    parts.append(f"H 940")
    return " ".join(parts)


def render_html(trace: Trace, results: tuple[Result, ...]) -> str:
    name = escape(trace.name)
    rows = [("Raw input", trace.edges, "#73a8ff")]
    rows.extend((result.algorithm.title(), result.events, color) for result, color in
                zip(results, ("#61dab3", "#ffba75")))
    height = 80 + 110 * len(rows)
    lines = []
    for tick in range(6):
        x = 150 + 158 * tick
        at = trace.duration_ms * tick / 5
        lines.append(f'<line x1="{x}" y1="45" x2="{x}" y2="{height - 45}" '
                     'stroke="#263449" stroke-dasharray="4 6"/>')
        lines.append(f'<text x="{x}" y="{height - 15}" text-anchor="middle">{at:g} ms</text>')
    for index, (label, edges, color) in enumerate(rows):
        y = 86 + index * 110
        lines.append(f'<text x="16" y="{y}" fill="{color}">{label}</text>')
        lines.append(f'<text x="130" y="{y - 16}" text-anchor="end">1</text>')
        lines.append(f'<text x="130" y="{y + 24}" text-anchor="end">0</text>')
        lines.append(f'<path d="{_path(edges, trace.initial_level, trace.duration_ms, index)}" '
                     f'fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/>')
    cards, tables = [], []
    for result in results:
        data = result.to_dict(trace.initial_level)
        label = result.algorithm.title()
        mismatch = data["final_level"] != (trace.edges[-1].level if trace.edges else trace.initial_level)
        note = '<p class="warning">Final output differs from raw input.</p>' if mismatch else ""
        cards.append(f'<section class="card"><h2>{label}</h2><p class="metric">'
                     f'{len(result.events)} <span>output transitions</span></p>'
                     f'<p>{data["presses"]} presses · {data["releases"]} releases · '
                     f'final level {data["final_level"]}</p>{note}</section>')
        event_rows = "".join(f'<tr><td>{edge.at_ms}</td><td>{edge.level}</td>'
                             f'<td>{"Press" if edge.level else "Release"}</td></tr>'
                             for edge in result.events)
        if not event_rows:
            event_rows = '<tr><td colspan="3">No output transitions</td></tr>'
        tables.append(f'<section><h2>{label} events</h2><table><caption class="sr-only">'
                      f'{label} output transitions</caption><thead><tr><th>Time (ms)</th>'
                      f'<th>Level</th><th>Meaning</th></tr></thead><tbody>{event_rows}</tbody></table></section>')
    raw_rows = "".join(f'<tr><td>{edge.at_ms}</td><td>{edge.level}</td></tr>' for edge in trace.edges)
    if not raw_rows:
        raw_rows = '<tr><td colspan="2">No input transitions</td></tr>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Debounce Lab — {name}</title><style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#0b111b;color:#e9eff9;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:48px 28px}}.eyebrow{{color:#61dab3;font-size:13px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}}
h1{{font-size:clamp(30px,5vw,48px);letter-spacing:-.035em;line-height:1.15;margin:12px 0 18px;overflow-wrap:anywhere}}h2{{font-size:19px;margin-top:0}}
p{{color:#b9c8dd}}.meta{{margin-bottom:30px}}.cards,.tables{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}}
.card,.plot{{background:#111c2a;border:1px solid #27364b;border-radius:16px;padding:24px}}.metric{{color:#fff;font-size:38px;margin:10px 0}}
.metric span{{font-size:15px;color:#b9c8dd}}.plot{{margin:24px 0 32px;padding:16px 12px}}.chart-scroll{{overflow-x:auto}}
svg{{width:100%;min-width:700px;height:auto;display:block}}svg text{{font:14px system-ui,sans-serif;fill:#b9c8dd}}.hint{{margin:0 12px 8px;font-size:14px}}
table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid #27364b}}th{{color:#b9c8dd;font-size:14px}}
.warning{{color:#ffba75}}.notes{{margin-top:32px;border-top:1px solid #27364b;padding-top:20px}}.sr-only{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}}
details{{margin-top:24px}}summary{{cursor:pointer}}@media(max-width:700px){{main{{padding:28px 16px}}.cards,.tables{{grid-template-columns:1fr}}}}
</style></head><body><main><div class="eyebrow">Debounce Lab / offline experiment</div>
<h1>{name}</h1><p class="meta">{trace.duration_ms} ms trace · {len(trace.edges)} raw transitions ·
{results[0].window_ms if results else 0} ms debounce window · initial level {trace.initial_level}</p>
<div class="cards">{"".join(cards)}</div><section class="plot"><h2 class="sr-only">Signal timeline</h2>
<div class="chart-scroll"><svg viewBox="0 0 980 {height}" role="img" aria-labelledby="chart-title chart-description">
<title id="chart-title">Raw input and debounced signals</title><desc id="chart-description">A step chart of digital levels. Exact times are available in the tables below.</desc>
{"".join(lines)}</svg></div><p class="hint">High = pressed. Low = released. Scroll the timeline horizontally on small screens.</p></section>
<div class="tables">{"".join(tables)}</div><details><summary>Raw input transitions</summary><table><thead><tr><th>Time (ms)</th><th>Level</th></tr></thead><tbody>{raw_rows}</tbody></table></details>
<section class="notes"><h2>Read the tradeoff</h2><p><strong>Stable</strong> waits for a quiet window after the most recent change. <strong>Lockout</strong> responds immediately, then ignores edges during its window; an ignored release can leave the output pressed.</p>
<p>This is a synthetic digital model, not a hardware measurement. Counts do not establish which edges represent human intent. A final-level mismatch may also mean the trace ended before a stable confirmation.</p>
<p>Deterministic report · no scripts, external assets, telemetry, or network requests.</p></section></main></body></html>
'''
