# RiftGuard

A Python reliability-event analyzer with a self-contained **offline reliability dashboard** for synthetic or user-authorized logs. It shows event frequency, recovery times, stages, repeated patterns, and trends by software version.

## Run and test

Requires Python 3.10+; standard library only at runtime.

    python -m pip install -e .
    python -m unittest discover -s tests -v
    python -m riftguard.cli data/sample_events.json --output riftguard-report.json --dashboard reliability-dashboard.html

Open the generated **reliability-dashboard.html** file in a browser, without any server or network connection.

The original JSON-to-stdout behavior still works:

    python -m riftguard.cli data/sample_events.json

## Dashboard metrics

- Error / critical event counts by event type and software version
- Event stage distribution and daily event-volume chart (UTC)
- Matched recovery counts and average recovery duration
- Repeated event signatures by version and type
- Interactive version selector filtering the dashboard's analysis

With the five fictional sample events, the dashboard reports **3 error/critical events, 2 recovered incidents, 19 seconds average recovery, and one repeated signature**.

## Privacy and limitations

The HTML embeds aggregate statistics, **not session IDs or event messages**. The original JSON report retains event details and should be reviewed before sharing. Version or event-type labels may still be proprietary. This offline educational prototype does not connect to any Riot Games service, identify root causes, or measure real-world failure rates. Recovery matching uses one pending error per session, and version filtering re-runs that heuristic on each subset.

See docs/dashboard.md for methodology. GitHub Actions tests Python 3.10–3.12 and validates JSON/HTML generation.