# RiftGuard — Reliability-event analysis and offline dashboard

**Python · Reliability engineering · Data analysis · Regression testing · CI/CD · Interactive HTML**

> **Scope:** An independent educational portfolio project for synthetic or explicitly authorized event records. No access to Riot Games services, no player telemetry integration, no production availability claims, and no claim to establish root causes.

## Project overview

RiftGuard turns structured reliability-event logs into reproducible event summaries, recovery-time estimates, and an offline interactive dashboard. It focuses on engineering discipline: validate inputs, make assumptions visible, test edge cases, and separate shareable summaries from raw event records.

| Dimension | Demonstrated capability |
| --- | --- |
| Analytics | Event counts, stages, severity filtering, repeated signatures by version and type |
| Recovery | Match a session's most recent outstanding error/critical event with the next recovery marker |
| Interface | Self-contained offline HTML with charts and software-version filtering |
| Reproducibility | Five-record baseline and 14-record multi-version fictional fixtures |
| Validation | 19 unit/integration tests, locally passing on Windows/Python 3.15 |
| Continuous integration | GitHub Actions successful on Python 3.10, 3.11, and 3.12 |
| Runtime | Python standard library; setuptools used for local package installation |

## 1. Problem and goals

Raw event streams make it difficult to answer basic questions consistently: **Which events occur repeatedly? Where are errors being recorded? How long do synthetic sessions appear to take to recover? What changes when the version label changes?**

The project creates a small, explainable analysis workflow rather than treating event correlations as proof of an incident's cause.

The implementation goals were to:

1. Validate required JSON fields and timezone-aware timestamps.
2. Summarize event counts, severity-filtered errors, stages, and repeated patterns.
3. Pair recovery events deterministically with prior session errors, without counting a duplicate recovery twice.
4. Support machine-readable JSON output and a browser-friendly offline dashboard.
5. Omit raw session IDs and free-text event messages from the dashboard HTML.

## 2. Architecture

~~~mermaid
flowchart LR
    A["Synthetic / authorized JSON logs"] --> B["CLI: src/riftguard/cli.py"]
    B --> C["Validation + matching: analyzer.py"]
    C --> D["JSON report: event-level details"]
    B --> E["Aggregation + rendering: dashboard.py"]
    E --> C
    E --> F["Standalone HTML: aggregate payload"]
    F --> G["Offline browser: filter, charts, table"]
    H["unittest fixtures"] -. checks .-> C
    H -. checks .-> E
    I["GitHub Actions: Python 3.10–3.12"] -. runs .-> H
~~~

The original CLI mode continues to emit JSON to standard output. Optional `--output` and `--dashboard` arguments write JSON and HTML separately. The HTML includes local CSS, JavaScript, and a serialized aggregate payload. No third-party JavaScript package or web server is necessary.

### Relevant source

| Source | Role |
| --- | --- |
| [Event analyzer](../src/riftguard/analyzer.py) | Timestamp validation, event counts, recovery matching |
| [Dashboard renderer](../src/riftguard/dashboard.py) | Aggregate metrics, UTC timeline, HTML output |
| [CLI](../src/riftguard/cli.py) | Commands, input/output paths, JSON/HTML generation |
| [Recovery regression tests](../tests/test_regressions.py) | Malformed severity, repeated recovery, separate incidents |
| [Dashboard tests](../tests/test_dashboard.py) | Offline HTML, sanitization, filtering, CLI, sample fixtures |
| [Multi-version sample](../data/version_comparison_events.json) | 14 fictional records across three software-version labels |

## 3. Key engineering decisions

**Transparent recovery heuristic.** RiftGuard tracks one latest outstanding error/critical event per session. A subsequent `recovered` event closes it; an extra recovery marker is not assigned again. This makes the result deterministic and testable. The tradeoff is that **concurrent failures in the same session are not represented independently**.

**Input validation.** Events require nonblank text fields, one of the supported severities, and an ISO-8601 timestamp containing a timezone. CLI output paths are checked so generating a report does not overwrite the input or write JSON and HTML into the same path.

**Analysis separate from visualization.** The dashboard reuses the existing analyzer for event interpretation and adds aggregation and presentation. Selecting one software version reanalyzes that version's records; cross-version recovery markers may therefore not match in the filtered result. The global version-comparison chart remains unfiltered for context.

**Portable presentation.** The HTML is a self-contained, static report. It can be inspected offline but does **not** subscribe to live events, issue alerts, or act as a monitoring service.

**Privacy-conscious exports.** The dashboard embeds aggregate statistics, version labels and event-type labels. It excludes raw session IDs and free-text messages; HTML string data is escaped and displayed through text nodes. **The JSON report still contains event-level records**, and even version/type labels may be sensitive in real logs. Any shared report needs review.

## 4. Reproduce the sample

Run from the repository root with Python 3.10+:

~~~powershell
python -m pip install -e .
python -m unittest discover -s tests -v

# Five-event baseline
python -m riftguard.cli data/sample_events.json --output riftguard-report.json --dashboard reliability-dashboard.html

# 14 fictional events across three versions and three UTC dates
python -m riftguard.cli data/version_comparison_events.json --output version-report.json --dashboard version-dashboard.html

Start-Process (Resolve-Path .\version-dashboard.html).Path
~~~

In the second example, select `All versions` or one of `0.4.1-demo`, `0.4.2-demo` and `0.5.0-demo` to explore the charts.

### Baseline fixture — verifiable results

| Metric | Synthetic sample |
| --- | ---: |
| Total event records | 5 |
| Error/critical event records | 3 |
| Matched recoveries | 2 |
| Login-timeout recovery | 18 seconds |
| Connection-loss recovery | 20 seconds |
| Mean matched recovery | 19 seconds |
| Repeated event signatures | 1 |

**Interpretation:** These are outputs for five invented records, not estimates of real crash rates, uptime, average player experiences, or system performance. No population or playtime denominator is available.

## 5. Verification and evidence

The repository was expanded from **three** original analyzer tests to **19** unit, regression, and dashboard/CLI tests.

- **Six core/regression tests:** counting and repeated signatures, recovery duration, timezone requirement, invalid severity, duplicate recovery suppression, and two separately recovered incidents.
- **Thirteen dashboard tests:** expected fixture aggregates, consistency with the original analyzer, version filtering, UTC normalization, empty/no-recovery handling, invalid input, omission of session identifiers/message text and script escaping, HTML generation, backward-compatible CLI behavior, JSON+HTML generation, output-path guards, and three-version fixture validation.
- **Local validation:** after the dashboard merge, Windows/Python 3.15 reported **19 tests passing in 0.422 seconds**, with a clean Git working tree.
- **CI validation:** the [GitHub Actions workflow](../.github/workflows/tests.yml) successfully ran installation, tests, JSON report checks, and HTML generation on Python **3.10, 3.11, 3.12**.

Passing tests support these specific claims; they do not demonstrate exhaustive correctness or production readiness. All provided records are synthetic.

## 6. Dashboard walkthrough and screenshot

The dashboard displays headline event metrics and panels for error types, stage distribution, daily UTC volume, recovery time by error category, global error counts by version, and repeated event signatures.

**Visual reference:** Generate the offline HTML from the fictional sample, open it in a browser, select **All versions**, and capture a screenshot if needed. Screenshot guidance lives in [docs/assets](assets/README.md). The reproducible HTML is the source of truth; do not substitute imagery that appears to be live Riot Games telemetry.

## 7. Limitations and next steps

**Model:** Only one outstanding error per session can be matched. The latest prior error wins, and a recovery marker is taken at face value; there is no independently validated incident classification or support for concurrent incident graphs.

**Evidence:** The 5- and 14-event fixtures are small and synthetic. There is no real incident dataset, ground-truth root-cause label, request/session denominator, ingestion coverage assessment, or benchmarking of production workloads.

**Operational scope:** No live ingestion, streaming, alerting, persistent database, telemetry agent, or account integration.

**Candidate follow-ups:** Add concurrent-incident tests and explicit unresolved-incident summaries; introduce larger synthetic fixtures and better error handling; evaluate accessibility and cross-browser rendering; document sharing/retention controls for future authorized datasets.

## 8. Engineering takeaway

RiftGuard demonstrates a complete **input → validate → analyze → test → aggregate → visualize** pipeline. The most important engineering outcome is not a large chart count; it is a small system whose calculations can be reproduced, assumptions can be inspected, failures can be regression-tested, and privacy boundaries can be explained.
