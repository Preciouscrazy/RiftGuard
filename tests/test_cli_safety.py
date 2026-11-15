"""CLI hard-link safety checks for the offline reliability analyzer."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CliSafetyTests(unittest.TestCase):
    def cli(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "riftguard.cli", *(str(x) for x in args)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=30,
        )

    def fixture(self, folder):
        source = Path(folder) / "events.json"
        source.write_bytes((ROOT / "data/sample_events.json").read_bytes())
        return source

    def linked(self, src, target):
        try:
            os.link(src, target)
        except OSError as exc:
            self.skipTest(f"Hard links unavailable: {exc}")

    def test_json_output_hardlink_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.fixture(temp)
            alias = Path(temp) / "report.json"
            self.linked(source, alias)
            old = source.read_bytes()
            result = self.cli(source, "--output", alias)
            self.assertEqual(result.returncode, 1)
            self.assertIn("overwrite input", result.stderr)
            self.assertEqual(source.read_bytes(), old)

    def test_html_output_hardlink_cannot_overwrite_input(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.fixture(temp)
            alias = Path(temp) / "dashboard.html"
            self.linked(source, alias)
            old = source.read_bytes()
            result = self.cli(source, "--dashboard", alias)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(source.read_bytes(), old)

    def test_json_and_dashboard_hardlink_collision(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.fixture(temp)
            report = Path(temp) / "report.json"
            dashboard = Path(temp) / "dashboard.html"
            report.write_text("untouched", encoding="utf-8")
            self.linked(report, dashboard)
            result = self.cli(source, "--output", report, "--dashboard", dashboard)
            self.assertEqual(result.returncode, 1)
            self.assertIn("different paths", result.stderr)
            self.assertEqual(report.read_text(encoding="utf-8"), "untouched")
            self.assertEqual(dashboard.read_text(encoding="utf-8"), "untouched")

    def test_distinct_report_and_dashboard_remain_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.fixture(temp)
            report = Path(temp) / "report.json"
            dashboard = Path(temp) / "dashboard.html"
            result = self.cli(source, "--output", report, "--dashboard", dashboard)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["events_analyzed"], 5)
            self.assertIn('id="timeline"', dashboard.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
