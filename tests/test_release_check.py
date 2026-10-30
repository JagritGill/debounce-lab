import unittest

from scripts.check_release import inspect_text


class ReleaseCheckTests(unittest.TestCase):
    def test_synthetic_credential_patterns(self):
        examples = [
            ("GitHub token", "ghp_" + "A" * 36),
            ("AWS access key", "AKIA" + "A" * 16),
            ("private key", "-----BEGIN " + "PRIVATE KEY-----"),
            ("service key", "sk-" + "A" * 30),
            ("credential URL", "https://" + "name:secret@example.invalid"),
            ("personal filesystem path", "/" + "Users/example/private/"),
            ("assigned credential", "api_key = '" + "A" * 20 + "'"),
        ]
        for label, value in examples:
            with self.subTest(label=label):
                self.assertIn(label, inspect_text(value))

    def test_ordinary_source_has_no_findings(self):
        self.assertEqual(inspect_text("def add(a, b): return a + b\n"), [])
