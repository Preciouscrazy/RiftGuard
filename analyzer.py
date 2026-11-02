from collections import Counter, defaultdict
from datetime import datetime

REQUIRED = {"timestamp", "version", "event_type", "stage", "severity", "session_id", "message"}
SEVERITIES = {"info", "warning", "error", "critical"}

def parse_time(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO 8601 string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value}") from exc
    if dt.tzinfo is None:
        raise ValueError("timestamp must include a timezone, e.g. Z")
    return dt

def analyze_events(events):
    if not isinstance(events, list):
        raise ValueError("Input must be a JSON array")
    parsed = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Each event must be an object")
        missing = REQUIRED - event.keys()
        if missing:
            raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
        for key in ("version", "event_type", "stage", "session_id", "message"):
            if not isinstance(event[key], str) or not event[key].strip():
                raise ValueError(f"{key} must be a non-empty string")
        if event["severity"] not in SEVERITIES:
            raise ValueError("Invalid severity: " + str(event["severity"]))
        row = dict(event); row["_time"] = parse_time(event["timestamp"]); parsed.append(row)
    parsed.sort(key=lambda row: row["_time"])
    event_counts, stage_counts, version_counts = Counter(), Counter(), Counter()
    errors, recoveries = defaultdict(list), defaultdict(list)
    for row in parsed:
        event_counts[row["event_type"]] += 1
        stage_counts[row["stage"]] += 1
        version_counts[(row["version"], row["event_type"])] += 1
        if row["severity"] in {"error", "critical"}: errors[row["session_id"]].append(row)
        if row["event_type"] == "recovered": recoveries[row["session_id"]].append(row)
    recovery_reports = []
    for session, recovery_rows in recoveries.items():
        for recovery in recovery_rows:
            prior = [err for err in errors[session] if err["_time"] <= recovery["_time"]]
            if prior:
                origin = prior[-1]
                recovery_reports.append({
                    "session_id": session, "error_type": origin["event_type"],
                    "error_stage": origin["stage"],
                    "recovery_seconds": round(max(0, (recovery["_time"] - origin["_time"]).total_seconds()), 2)
                })
    repeated = [{"version": v, "event_type": t, "count": n,
                 "signal": "Repeated event; inspect surrounding logs."}
                for (v, t), n in sorted(version_counts.items()) if n >= 2 and t != "recovered"]
    public_events = [{k:v for k,v in row.items() if k != "_time"} for row in parsed]
    return {"project":"RiftGuard", "events_analyzed":len(parsed),
            "event_counts":dict(sorted(event_counts.items())),
            "stage_counts":dict(sorted(stage_counts.items())),
            "recovery_reports":recovery_reports, "repeated_patterns":repeated,
            "events":public_events,
            "notice":"Patterns are investigation signals, not proof of root cause."}
