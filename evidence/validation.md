# RiftGuard — reproducible validation

**Scope:** Synthetic/authorized log analysis and a self-contained offline dashboard. Results are investigation signals, not root-cause attribution or production failure-rate measurements.

## Before this cleanup
- The previous [successful Ubuntu GitHub Actions run #42190658592](https://github.com/Preciouscrazy/RiftGuard/actions/runs/42190658592) covered Python 3.10, 3.11 and 3.12.
- The 19-test suite had documented local Windows/Python 3.15 validation. The old `VERIFICATION.md` showed only an earlier three-test snapshot and is removed from this cleanup.
- The baseline and multi-version sample fixtures contain **5** and **14** fictional event records.

## Targeted changes
- Add **four CLI regression methods** checking that JSON/HTML output paths never overwrite the JSON input (including existing hard links), reject hard-linked JSON/HTML collisions, and preserve valid dual-output behavior.
- Keep the original event analyzer, incident-pairing heuristic, dashboard HTML, and sample fixtures unchanged.
- Exercise the upgraded **23-test** suite and generated JSON/HTML artifacts on Windows and Ubuntu using Python 3.10–3.12.

## Reproduce
```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m riftguard.cli data/sample_events.json --output sample-report.json --dashboard reliability-dashboard.html
python -m riftguard.cli data/version_comparison_events.json --output version-report.json --dashboard version-dashboard.html
```

The dashboard serializes aggregate visualizations but not raw session IDs or free-text event messages; the JSON report retains event details. Do not share user or proprietary logs.

## GitHub-hosted verification

| Environment | Python 3.10 | Python 3.11 | Python 3.12 |
| --- | --- | --- | --- |
| Ubuntu 24.04 | Pending | Pending | Pending |
| Windows latest | Pending | Pending | Pending |

**Not yet verified for this branch.** Record the exact hosted run results after the PR-head matrix finishes.
