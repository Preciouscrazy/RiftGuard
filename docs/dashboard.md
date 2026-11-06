# RiftGuard Reliability Dashboard

Generate from the repository root:

    python -m pip install -e .
    python -m riftguard.cli data/sample_events.json --output riftguard-report.json --dashboard reliability-dashboard.html

In PowerShell, open the file with:

    Start-Process (Resolve-Path .\reliability-dashboard.html).Path

No server, external script, CDN, network access, or account integration is needed.

**Metrics:** event errors are counts of error/critical-severity rows, not distinct users or incidents. Recovery durations follow the existing single-pending-error-per-session matching heuristic. Average recovery is N/A if no recovery was matched. Repeated signatures combine version and event type appearing at least twice. The daily timeline uses UTC calendar dates, omitting days without events. The version comparison chart always uses the full input; other panels update on selection. Each filtered scope reruns the original heuristic, so a recovery in a different version may not match.

**Privacy:** the HTML embeds aggregate summaries only (not session IDs or message bodies). Version/event type labels remain visible. Review the original JSON report, which contains raw event details, before sharing.

All sample inputs are synthetic. Error frequency here is not an operational error rate and does not establish cause. For production reliability analysis, validate incident models, telemetry coverage, safe data retention, and denominator quality.