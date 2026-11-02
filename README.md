# RiftGuard
A Python reliability-event analyzer for **synthetic or authorized logs**. It summarizes event frequency, stages, repeated event patterns by version, and simple time-to-recovery estimates. This is an observability demo, not a root-cause oracle.

Run:
```bash
python -m riftguard.cli data/sample_events.json
python -m unittest discover -s tests -v
```
Python 3.10+; no third-party dependencies. Timestamps must be ISO 8601 with timezone (for example `Z`). Each event includes `timestamp`, `version`, `event_type`, `stage`, `severity`, `session_id`, and `message`.

A `recovered` event is matched to the latest preceding error/critical event in that session. Repeated events are signals for investigation, not proof of cause. Do not access private Riot services or other players' private telemetry.

## Development

Run the unit tests before publishing changes:

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs the same test suite for pushes and pull requests.

## Scope and limitations

This project demonstrates documented educational analysis with sample data. Its results should not be treated as production monitoring, real-world player ratings, or access to any proprietary game service.
