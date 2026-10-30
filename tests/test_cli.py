from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from debounce_lab.engine import compare
from debounce_lab.model import Edge, Trace
from debounce_lab.report import render_html

ROOT = Path(__file__).resolve().parents[1]


class MarkupInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend(attrs)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "debounce_lab", *map(str, args)],
                              cwd=ROOT, text=True, capture_output=True, check=False)

    def test_text_demo(self):
        result = self.run_cli("examples/bouncy-button.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stable: [32:1, 118:0] | presses=1 releases=1 final=0", result.stdout)
        self.assertIn("lockout: [10:1, 100:0]", result.stdout)

    def test_json_demo_is_repeatable(self):
        first = self.run_cli("examples/short-tap.json", "--format", "json")
        second = self.run_cli("examples/short-tap.json", "--format", "json")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        results = json.loads(first.stdout)["results"]
        self.assertEqual([result["final_level"] for result in results], [0, 1])

    def test_html_file_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.html"
            args = ("examples/bouncy-button.json", "--format", "html", "--output", target)
            first = self.run_cli(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = target.read_bytes()
            second = self.run_cli(*args)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(target.read_bytes(), before)
            self.assertIn(b"<svg", before)

    def test_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "trace.json"
            original = (ROOT / "examples/short-tap.json").read_bytes()
            target.write_bytes(original)
            result = self.run_cli(target, "--output", target)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_bytes(), original)

    def test_missing_file_and_invalid_window(self):
        for args in (("does-not-exist.json",), ("examples/short-tap.json", "--window-ms", "0")):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_bad_json_and_size_limit(self):
        payloads = [b"{", b"\xff", b'{"name": "a", "name": "b"}',
                    b" " * 2_000_001, b"[" * 2_000 + b"]" * 2_000]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "trace.json"
            for payload in payloads:
                target.write_bytes(payload)
                result = self.run_cli(target)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_html_escapes_input_and_has_no_active_content(self):
        trace = Trace('<img src=x onerror="alert(1)"> & <script>bad</script>', 60, 0,
                      (Edge(10, 1), Edge(15, 0)))
        html = render_html(trace, compare(trace, 12))
        self.assertIn("&lt;img", html)
        self.assertIn("Final output differs from raw input.", html)
        inspector = MarkupInspector()
        inspector.feed(html)
        self.assertFalse(set(inspector.tags) & {"script", "img", "iframe", "link", "object"})
        self.assertFalse(any(key.startswith("on") or key in {"src", "href"} for key, _ in inspector.attributes))
        self.assertIn("Content-Security-Policy", html)

    def test_html_determinism(self):
        trace = Trace("repeatable", 30, 0, (Edge(1, 1),))
        self.assertEqual(render_html(trace, compare(trace, 12)), render_html(trace, compare(trace, 12)))
