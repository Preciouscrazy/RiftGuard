"""Self-contained offline reliability dashboard with aggregate-only embedded data."""
from collections import Counter, defaultdict
from datetime import timezone
import json
from pathlib import Path
from .analyzer import analyze_events, parse_time


def _rows(counts):
    return [{"label": k, "count": v} for k, v in sorted(counts.items(), key=lambda p: (-p[1], p[0]))]


def _summary(events):
    analysis = analyze_events(events)
    records = analysis["events"]
    errors = [r for r in records if r["severity"] in ("error", "critical")]
    recoveries = analysis["recovery_reports"]
    durations = [r["recovery_seconds"] for r in recoveries]
    by_kind = defaultdict(list)
    for r in recoveries:
        by_kind[r["error_type"]].append(r["recovery_seconds"])
    timeline = Counter(parse_time(r["timestamp"]).astimezone(timezone.utc).date().isoformat() for r in records)
    return {
        "total_events": len(records),
        "error_events": len(errors),
        "recovered_incidents": len(recoveries),
        "mean_recovery_seconds": round(sum(durations)/len(durations), 2) if durations else None,
        "repeated_signals": len(analysis["repeated_patterns"]),
        "error_types": _rows(Counter(r["event_type"] for r in errors)),
        "stages": _rows(analysis["stage_counts"]),
        "error_counts_by_version": _rows(Counter(r["version"] for r in errors)),
        "timeline": [{"date": d, "count": n} for d, n in sorted(timeline.items())],
        "recovery_types": [{"label": kind, "mean_seconds": round(sum(vals)/len(vals), 2), "count": len(vals)}
                           for kind, vals in sorted(by_kind.items())],
        "repeated_patterns": [{"version": r["version"], "event_type": r["event_type"], "count": r["count"]}
                              for r in analysis["repeated_patterns"]],
    }


def build_dashboard_data(events):
    """Re-run existing analysis per version; never embed session IDs or messages."""
    overall = _summary(events)
    versions = sorted({event["version"] for event in events}) if events else []
    return {
        "versions": versions,
        "overall": overall,
        "by_version": {v: _summary([e for e in events if e["version"] == v]) for v in versions},
        "limitations": ("Synthetic or authorized logs only. Incident matching uses a single outstanding "
                        "error per session; version filters re-run the heuristic on that subset. "
                        "Repeated patterns are investigation signals, not proven causes. "
                        "Event counts are not real-world failure rates."),
    }


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>RiftGuard | Reliability Lab</title>
<style>
:root{color-scheme:dark;--bg:#0a0d1d;--card:#171b36;--edge:#394362;--text:#f7f7ff;--muted:#c7cee5;--purple:#ba98ff;--cyan:#70dce9}
*{box-sizing:border-box}body{margin:0;padding:36px 18px;font:15px/1.5 system-ui,Segoe UI,sans-serif;color:var(--text);background:radial-gradient(ellipse at 85% 0%,#312052 0%,transparent 48%),var(--bg);min-height:100vh}
main{max-width:1100px;margin:auto}h1{font-size:clamp(2.4rem,6vw,3.7rem);letter-spacing:-.045em;margin:0}h2{font-size:1.15rem;margin:0 0 12px}p,small{color:var(--muted)}header{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap}.eyebrow{color:var(--cyan);font-weight:700;letter-spacing:.16em;text-transform:uppercase;font-size:.8rem}
select{margin-top:6px;padding:10px 14px;color:#fff;border-radius:10px;background:#252c4d;border:1px solid #7b86a5;font:inherit}select:focus-visible{outline:3px solid var(--cyan)}
.warning{padding:13px 17px;border:1px solid #8468a7;border-left:4px solid var(--purple);background:#302443;border-radius:13px;margin:24px 0}
.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:20px 0}.metric,.card{background:rgba(23,27,54,.95);border:1px solid var(--edge);border-radius:17px;padding:20px}.metric strong{font-size:clamp(1.4rem,2.7vw,2rem);display:block;font-variant-numeric:tabular-nums}.cards{display:grid;grid-template-columns:1fr 1fr;gap:15px}.wide{grid-column:span 2}.bar{display:grid;grid-template-columns:minmax(90px,1fr) 2fr 48px;gap:10px;align-items:center;margin:12px 0}.barname{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.track{height:12px;border-radius:99px;background:#35405f;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,var(--purple),var(--cyan));border-radius:99px}.barcount{text-align:right;font-variant-numeric:tabular-nums}.blank{padding:16px 0;color:var(--muted)}svg{width:100%;height:auto;max-height:245px}.axis{font-size:12px;fill:var(--muted)}table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{padding:10px;text-align:left;border-bottom:1px solid var(--edge)}td:last-child,th:last-child{text-align:right}th{color:var(--muted)}.tablewrap{overflow-x:auto}footer{padding:26px 0;color:var(--muted);font-size:.86rem}
@media(max-width:800px){.metrics{grid-template-columns:repeat(3,1fr)}}@media(max-width:600px){.metrics{grid-template-columns:repeat(2,1fr)}.cards{grid-template-columns:1fr}.wide{grid-column:span 1}}
</style></head><body><main>
<header><div><div class="eyebrow">RiftGuard / Offline Observability</div><h1>Reliability Lab</h1><p>Error frequency, incident recovery, and version-based patterns.</p></div><div><label for="version">Version filter</label><div><select id="version"></select></div></div></header>
<div class="warning"><strong>Educational analysis only.</strong> Uses synthetic or authorized logs. No live Riot Games connections or root-cause claims.</div>
<section class="metrics" aria-live="polite">
<div class="metric"><small>Events analyzed</small><strong id="total">—</strong></div>
<div class="metric"><small>Error / critical</small><strong id="errors">—</strong></div>
<div class="metric"><small>Recoveries matched</small><strong id="recovered">—</strong></div>
<div class="metric"><small>Mean recovery</small><strong id="average">—</strong></div>
<div class="metric"><small>Repeated signatures</small><strong id="repeats">—</strong></div>
</section>
<div class="cards">
<section class="card"><h2>Error events by type</h2><p>Event counts for error or critical severity.</p><div id="error-types"></div></section>
<section class="card"><h2>Events by stage</h2><p>Count of all events in each stage.</p><div id="stages"></div></section>
<section class="card wide"><h2>Daily event volume (UTC)</h2><p>Days without recorded events are omitted.</p><svg id="timeline" viewBox="0 0 800 240" role="img" aria-label="Daily event count chart"></svg></section>
<section class="card"><h2>Recovery durations</h2><p>Mean recovery seconds by originating error type.</p><div id="recoveries"></div></section>
<section class="card"><h2>Errors by version</h2><p>Global comparison; unaffected by selected version.</p><div id="versions"></div></section>
<section class="card wide"><h2>Repeated event patterns</h2><p>Same version and event type at least twice.</p><div class="tablewrap"><table><thead><tr><th>Version</th><th>Event type</th><th>Count</th></tr></thead><tbody id="patterns"></tbody></table></div></section>
</div><footer id="notice"></footer></main>
<script id="dashboard-data" type="application/json">__DATA__</script>
<script>
(function(){"use strict";
const data=JSON.parse(document.getElementById("dashboard-data").textContent),select=document.getElementById("version"),svg=document.getElementById("timeline"),ns="http://www.w3.org/2000/svg";
for(const name of ["All versions",...data.versions]){const option=document.createElement("option");option.textContent=name;option.value=name;select.appendChild(option)}
function put(id,value){document.getElementById(id).textContent=String(value)}
function bars(id,rows,key="count",unit=""){const parent=document.getElementById(id);parent.replaceChildren();if(!rows.length){const p=document.createElement("p");p.className="blank";p.textContent="No observations";parent.appendChild(p);return}
 const peak=Math.max(1,...rows.map(x=>x[key]));for(const row of rows){const div=document.createElement("div");div.className="bar",label=document.createElement("span");label.className="barname";label.textContent=row.label;label.title=row.label;
 const rail=document.createElement("div");rail.className="track";const fill=document.createElement("div");fill.className="fill";fill.style.width=100*row[key]/peak+"%";rail.appendChild(fill);
 const value=document.createElement("span");value.className="barcount";value.textContent=row[key]+unit;div.append(label,rail,value);parent.appendChild(div)}}
function make(tag,attrs,parent=svg){const e=document.createElementNS(ns,tag);for(const key of Object.keys(attrs))e.setAttribute(key,String(attrs[key]));parent.appendChild(e);return e}
function timeline(rows){svg.replaceChildren();if(!rows.length){const t=make("text",{x:400,y:120,"text-anchor":"middle",class:"axis"});t.textContent="No events";return}
 const top=Math.max(...rows.map(r=>r.count),1),left=46,right=786,bottom=186,height=150,width=(right-left)/rows.length;
 for(const tick of [0,.5,1]){const y=bottom-tick*height;make("line",{x1:left,x2:right,y1:y,y2:y,stroke:"#374263"});const t=make("text",{x:left-6,y:y+4,"text-anchor":"end",class:"axis"});t.textContent=String(Math.round(top*tick))}
 rows.forEach((r,i)=>{const x=left+width*(i+.5),h=height*r.count/top;const bar=make("rect",{x:x-Math.min(45,width*.56)/2,y:bottom-h,width:Math.min(45,width*.56),height:h,rx:4,fill:"#ba98ff"});const tip=make("title",{},bar);tip.textContent=r.date+": "+r.count+" event(s)";const label=make("text",{x,y:213,"text-anchor":"middle",class:"axis"});label.textContent=rows.length<=8?r.date.slice(5):String(i+1)})}
function table(rows){const body=document.getElementById("patterns");body.replaceChildren();if(!rows.length){const tr=document.createElement("tr"),td=document.createElement("td");td.colSpan=3;td.textContent="No repeated patterns";tr.appendChild(td);body.appendChild(tr);return}
 for(const entry of rows){const tr=document.createElement("tr");for(const val of [entry.version,entry.event_type,entry.count]){const td=document.createElement("td");td.textContent=String(val);tr.appendChild(td)}body.appendChild(tr)}}
function render(){const current=select.selectedIndex===0?data.overall:data.by_version[select.value];put("total",current.total_events);put("errors",current.error_events);put("recovered",current.recovered_incidents);
 put("average",current.mean_recovery_seconds===null?"N/A":current.mean_recovery_seconds.toFixed(2)+" s");put("repeats",current.repeated_signals);
 bars("error-types",current.error_types);bars("stages",current.stages);bars("recoveries",current.recovery_types,"mean_seconds"," s");bars("versions",data.overall.error_counts_by_version);timeline(current.timeline);table(current.repeated_patterns);put("notice",data.limitations+" HTML contains aggregates only, not session IDs or messages.")}
select.addEventListener("change",render);render();
})();
</script></body></html>'''


def render_dashboard(events):
    payload = json.dumps(build_dashboard_data(events), allow_nan=False, ensure_ascii=True, separators=(",", ":"))
    for key, replacement in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")):
        payload = payload.replace(key, replacement)
    return _HTML.replace("__DATA__", payload)


def save_dashboard(events, destination):
    path = Path(destination)
    path.write_text(render_dashboard(events), encoding="utf-8")
    return path
