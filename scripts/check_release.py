"""Small, local release-scope and credential-pattern check. No network access.

This is a heuristic aid, not a proof that arbitrary files are secret-free or
original. Review the source inventory and provenance separately before release.
"""

import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", "__pycache__", "out", ".venv", "coverage"}
ROOT_FILES = {"AGENTS.md", "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", ".gitignore"}
SOURCE_DIRS = {"debounce_lab", "tests", "scripts", "examples", "docs", ".github"}
SUFFIXES = {".py", ".json", ".md", ".yml", ".html"}
PATTERNS = {
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "service key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"),
    "credential URL": re.compile(r"https?://[^\s/@]+:[^\s/@]+@"),
    "personal filesystem path": re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/"),
    "assigned credential": re.compile(
        r'''(?i)(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*["'][A-Za-z0-9_+/.=-]{12,}["']'''
    ),
}


def inspect_text(text: str) -> list[str]:
    return [label for label, pattern in PATTERNS.items() if pattern.search(text)]


def main() -> int:
    findings, checked = [], []
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if any(part in IGNORE_DIRS for part in relative.parts):
            continue
        if path.is_symlink():
            findings.append(f"{relative}: symlink is outside release policy")
            continue
        if path.is_dir() or path.name == ".DS_Store":
            continue
        allowed = (len(relative.parts) == 1 and path.name in ROOT_FILES) or (
            len(relative.parts) > 1 and relative.parts[0] in SOURCE_DIRS and path.suffix in SUFFIXES
        )
        if not allowed:
            findings.append(f"{relative}: unexpected release file")
            continue
        if path.stat().st_size > 2_000_000:
            findings.append(f"{relative}: unexpected file size")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            findings.append(f"{relative}: non-text file")
            continue
        if "\x00" in text:
            findings.append(f"{relative}: binary content")
        findings.extend(f"{relative}: {label}" for label in inspect_text(text))
        if relative.parts[0] == "debounce_lab" and path.suffix == ".py":
            for node in ast.walk(ast.parse(text)):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [name.name.split(".")[0] for name in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    modules = [(node.module or "").split(".")[0]]
                for module in modules:
                    if module not in sys.stdlib_module_names:
                        findings.append(f"{relative}: non-standard dependency {module}")
                    if module in {"socket", "urllib", "http", "subprocess"}:
                        findings.append(f"{relative}: network/process import requires review")
        checked.append(relative.as_posix())
    if findings:
        print("Release check failed (values are redacted):")
        print("\n".join(findings))
        return 1
    print(f"PASS: {len(checked)} release files; no matching credential patterns, personal paths, or unexpected files.")
    print("PASS: runtime imports are standard-library/local modules; no network/process imports.")
    print("Heuristic check only. Review provenance and the exact staged file list before publishing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
