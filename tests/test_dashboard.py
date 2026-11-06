"""Regression tests for the portable offline reliability dashboard."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from riftguard.analyzer import analyze_events
from riftguard.dashboard import build_dashboard_data, render_dashboard, save_dashboard


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = json.loads((ROOT / "data" / "sample_events.json").read_text(encoding="utf-8"))

    @staticmethod
    def event(version="v1", event_type="timeout", severity="error", session="s1", timestamp="2026-10-27T18:00:00Z", message="demo"):
        return {"timestamp": timestamp, "version": version, "event_type": event_type,
                "stage": "match", "severity": severity, "session_id": session, "message": message}

    def test_sample_aggregates(self):
        data = build_dashboard_data(self.events)["overall"]
        self.assertEqual((data["total_events"], data["error_events"], data["recovered_incidents"]), (5, 3, 2))
        self.assertEqual(data["mean_recovery_seconds"], 19.0)
        self.assertEqual(data["error_types"][0], {"label": "connection_lost", "count": 2})
        self.assertEqual(data["repeated_patterns"][0]["count"], 2)

    def test_original_analyzer_unchanged(self):
        report = analyze_events(self.events)
        dashboard = build_dashboard_data(self.events)["overall"]
        self.assertEqual(report["events_analyzed"], dashboard["total_events"])
        self.assertEqual(len(report["recovery_reports"]), dashboard["recovered_incidents"])

    def test_version_filter(self):
        sample = [self.event("v1", session="one"), self.event("v2", session="two"),
                  self.event("v2", "recovered", "info", "two", "2026-10-27T18:00:20Z")]
        data = build_dashboard_data(sample)
        self.assertEqual(data["versions"], ["v1", "v2"])
        self.assertEqual(data["by_version"]["v1"]["recovered_incidents"], 0)
        self.assertEqual(data["by_version"]["v2"]["recovered_incidents"], 1)

    def test_timezone_conversion(self):
        data = build_dashboard_data([self.event(timestamp="2026-10-27T23:30:00-05:00")])
        self.assertEqual(data["overall"]["timeline"], [{"date": "2026-10-28", "count": 1}])

    def test_undefined_recovery_and_empty_events(self):
        data = build_dashboard_data([self.event()])
        self.assertIsNone(data["overall"]["mean_recovery_seconds"])
        self.assertEqual(data["overall"]["recovery_types"], [])
        self.assertEqual(build_dashboard_data([])["overall"]["total_events"], 0)

    def test_invalid_input_rejected(self):
        bad = self.event()
        bad["severity"] = ["error"]
        with self.assertRaises(ValueError):
            build_dashboard_data([bad])

    def test_html_offline_and_private(self):
        malicious = self.event(version="<script>alert(1)</script>", session="SESSION-SECRET", message="MESSAGE-SECRET")
        html = render_dashboard([malicious])
        self.assertIn('id="version"', html)
        self.assertIn('id="timeline"', html)
        self.assertNotIn("SESSION-SECRET", html)
        self.assertNotIn("MESSAGE-SECRET", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("\\u003cscript", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("https://", html)
        payload = re.search(r'<script id="dashboard-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(payload)
        self.assertEqual(json.loads(payload.group(1))["versions"], ["<script>alert(1)</script>"])

    def test_html_output_written(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dashboard.html"
            save_dashboard(self.events, path)
            self.assertIn("Reliability Lab", path.read_text(encoding="utf-8"))

    def run_cli(self, *arguments):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run([sys.executable, "-m", "riftguard.cli", *map(str, arguments)],
                              cwd=ROOT, env=env, capture_output=True, text=True, check=False)

    def test_original_cli_mode(self):
        r = self.run_cli(ROOT / "data" / "sample_events.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["events_analyzed"], 5)

    def test_cli_writes_html_and_json(self):
        with tempfile.TemporaryDirectory() as folder:
            json_path, html_path = Path(folder) / "report.json", Path(folder) / "dashboard.html"
            r = self.run_cli(ROOT / "data" / "sample_events.json", "--output", json_path, "--dashboard", html_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(json_path.read_text())["events_analyzed"], 5)
            self.assertIn("Reliability Lab", html_path.read_text())

    def test_cli_rejects_same_output(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "same.html"
            r = self.run_cli(ROOT / "data" / "sample_events.json", "--output", target, "--dashboard", target)
            self.assertEqual(r.returncode, 1)
            self.assertFalse(target.exists())

    def test_cli_refuses_input_overwrite(self):
        r = self.run_cli(ROOT / "data" / "sample_events.json", "--output", ROOT / "data" / "sample_events.json")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
