from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _script_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_html(report: dict[str, Any], collection: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    features_json = _script_json(collection.get("features", []))
    report_json = _script_json(report)
    rows = []
    for issue in report["issues"]:
        ev = issue["evidence"]
        page = f", p. {ev['page']}" if ev.get("page") is not None else ""
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(issue['rule_id'])}</code></td>"
            f"<td>{html.escape(str(issue.get('feature_id') or 'dataset'))}</td>"
            f"<td>{html.escape(issue['message'])}</td>"
            f"<td>{html.escape(ev['document'])} § {html.escape(ev['section'])}{page}</td>"
            f"<td>{html.escape(issue['severity'])}</td>"
            "</tr>"
        )
    summary = report["summary"]
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NMA validation report</title>
<style>
:root{{--ink:#15202b;--muted:#64748b;--panel:#fff;--bg:#f1f5f9;--bad:#b42318;--good:#067647;--accent:#155eef}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
header{{padding:28px 5vw;background:#0f172a;color:white}}main{{max-width:1200px;margin:24px auto;padding:0 20px}}
.grid{{display:grid;grid-template-columns:1.1fr .9fr;gap:20px}}.panel{{background:white;border-radius:12px;padding:20px;box-shadow:0 1px 3px #0002}}
.stats{{display:flex;gap:12px;flex-wrap:wrap}}.stat{{padding:10px 14px;border-radius:8px;background:#f8fafc}}.stat b{{font-size:22px;display:block}}
svg{{width:100%;height:420px;background:#eaf3f8;border-radius:8px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:9px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}}
th{{color:var(--muted)}}code{{font-size:12px}}.failed{{color:var(--bad)}}.passed{{color:var(--good)}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
</style></head>
<body><header><h1>National Map Agent — validation evidence</h1><p>{html.escape(report["dataset"])}</p></header>
<main><section class="panel"><h2 class="{html.escape(report["status"])}">{html.escape(report["status"].replace("_", " ").title())}</h2>
<div class="stats"><div class="stat"><b>{summary["features"]}</b>features</div><div class="stat"><b>{summary["rules_evaluated"]}</b>rules</div><div class="stat"><b>{summary["errors"]}</b>errors</div><div class="stat"><b>{summary["warnings"]}</b>warnings</div></div></section>
<div class="grid" style="margin-top:20px"><section class="panel"><h2>Spatial findings</h2><svg id="map" viewBox="0 0 800 420" aria-label="Dataset preview"></svg></section>
<section class="panel"><h2>Specification</h2><p><b>{html.escape(report["specification"]["title"])}</b><br>Version {html.escape(report["specification"]["version"])}<br>Layer {html.escape(report["layer"])}</p><p>Every finding below is produced by a deterministic check and linked to evidence.</p></section></div>
<section class="panel" style="margin-top:20px"><h2>Issues and evidence</h2><div style="overflow:auto"><table><thead><tr><th>Rule</th><th>Feature</th><th>Finding</th><th>Evidence</th><th>Severity</th></tr></thead><tbody>{"".join(rows) or '<tr><td colspan="5">No issues</td></tr>'}</tbody></table></div></section></main>
<script>const features={features_json}, report={report_json};
const svg=document.getElementById('map'), NS='http://www.w3.org/2000/svg';
const points=features.flatMap(f=>{{if(!f.geometry)return[];return f.geometry.type==='Point'?[f.geometry.coordinates]:f.geometry.type==='LineString'?f.geometry.coordinates:[]}});
if(points.length){{const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);const sx=x=>40+(x-minx)/(maxx-minx||1)*720,sy=y=>380-(y-miny)/(maxy-miny||1)*340;
features.forEach((f,i)=>{{if(!f.geometry)return;const id=f.properties&&f.properties.feature_id;const bad=report.issues.some(x=>x.feature_index===i||(x.feature_id&&x.feature_id===id));if(f.geometry.type==='LineString'){{const p=document.createElementNS(NS,'polyline');p.setAttribute('points',f.geometry.coordinates.map(q=>sx(q[0])+','+sy(q[1])).join(' '));p.setAttribute('fill','none');p.setAttribute('stroke',bad?'#b42318':'#067647');p.setAttribute('stroke-width','6');p.setAttribute('stroke-linecap','round');svg.appendChild(p)}}else if(f.geometry.type==='Point'){{const p=document.createElementNS(NS,'circle');p.setAttribute('cx',sx(f.geometry.coordinates[0]));p.setAttribute('cy',sy(f.geometry.coordinates[1]));p.setAttribute('r','9');p.setAttribute('fill',bad?'#b42318':'#067647');p.setAttribute('stroke','white');p.setAttribute('stroke-width','3');svg.appendChild(p)}}}})}}
</script></body></html>"""
    target.write_text(document, encoding="utf-8")
    return target
