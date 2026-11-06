import unittest
from riftguard.analyzer import analyze_events

def event(ts, kind, severity="error"):
    return {"timestamp":ts,"version":"demo","event_type":kind,"stage":"match","severity":severity,"session_id":"s1","message":"synthetic"}

class Tests(unittest.TestCase):
    def test_counts_and_repeated_patterns(self):
        r = analyze_events([event("2026-10-27T18:00:00Z","network_error"), event("2026-10-27T18:00:10Z","network_error")])
        self.assertEqual(r["event_counts"]["network_error"], 2)
        self.assertEqual(len(r["repeated_patterns"]), 1)
    def test_recovery_duration(self):
        r = analyze_events([event("2026-10-27T18:00:00Z","crash","critical"), event("2026-10-27T18:00:12Z","recovered","info")])
        self.assertEqual(r["recovery_reports"][0]["recovery_seconds"], 12.0)
    def test_timezone_required(self):
        with self.assertRaises(ValueError): analyze_events([event("2026-10-27T18:00:00","crash")])
if __name__ == "__main__": unittest.main()
