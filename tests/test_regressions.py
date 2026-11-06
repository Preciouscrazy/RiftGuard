import unittest
from riftguard.analyzer import analyze_events


def event(timestamp, event_type, severity="error"):
    return {
        "timestamp": timestamp,
        "version": "demo",
        "event_type": event_type,
        "stage": "match",
        "severity": severity,
        "session_id": "synthetic-001",
        "message": "Synthetic test event",
    }


class RegressionTests(unittest.TestCase):

    def test_reject_unhashable_severity(self):
        sample = event(
            "2026-10-27T18:00:00Z",
            "connection_lost",
            ["error"],
        )
        with self.assertRaises(ValueError):
            analyze_events([sample])

    def test_duplicate_recovery_not_counted_twice(self):
        events = [
            event("2026-10-27T18:00:00Z", "connection_lost"),
            event("2026-10-27T18:00:20Z", "recovered", "info"),
            event("2026-10-27T18:00:30Z", "recovered", "info"),
        ]
        report = analyze_events(events)
        self.assertEqual(len(report["recovery_reports"]), 1)
        self.assertEqual(
            report["recovery_reports"][0]["recovery_seconds"],
            20.0,
        )

    def test_separate_incidents_can_recover(self):
        events = [
            event("2026-10-27T18:00:00Z", "connection_lost"),
            event("2026-10-27T18:00:05Z", "recovered", "info"),
            event("2026-10-27T18:00:10Z", "connection_lost"),
            event("2026-10-27T18:00:25Z", "recovered", "info"),
        ]
        report = analyze_events(events)
        durations = [
            item["recovery_seconds"]
            for item in report["recovery_reports"]
        ]
        self.assertEqual(durations, [5.0, 15.0])


if __name__ == "__main__":
    unittest.main()