#!/usr/bin/env python3
"""Generate the SlotSync Grafana dashboard JSON.

Writing the dashboard as code keeps it reviewable in pull requests; the output
is committed to helm/slotsync/dashboards/slotsync.json and shipped by the chart.
    python3 monitoring/build_dashboard.py
"""

import json
from pathlib import Path

DS = {"type": "prometheus", "uid": "${datasource}"}
NS = 'namespace="$namespace"'
API = f'{NS}, handler!~"/metrics|/health|/ready"'
_id = 0
panels = []


def panel(kind, title, targets, x, y, w, h, unit="short", **extra):
    global _id
    _id += 1
    p = {
        "id": _id,
        "type": kind,
        "title": title,
        "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [
            {"refId": chr(65 + i), "datasource": DS, "expr": expr, "legendFormat": legend}
            for i, (expr, legend) in enumerate(targets)
        ],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
    }
    if kind == "timeseries":
        p["fieldConfig"]["defaults"]["custom"] = {
            "drawStyle": "line",
            "lineWidth": 2,
            "fillOpacity": 12,
            "gradientMode": "opacity",
            "showPoints": "never",
            "stacking": {"mode": extra.pop("stack", "none")},
        }
        p["options"] = {
            "legend": {"displayMode": "list", "placement": "bottom", "calcs": []},
            "tooltip": {"mode": "multi", "sort": "desc"},
        }
    if kind == "stat":
        p["options"] = {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": "background",
            "graphMode": "area",
            "textMode": "value",
        }
        p["fieldConfig"]["defaults"]["thresholds"] = {
            "mode": "absolute",
            "steps": extra.pop("steps", [{"color": "green", "value": None}]),
        }
        p["fieldConfig"]["defaults"]["color"] = {"mode": "thresholds"}
    p["fieldConfig"]["defaults"].update(extra)
    panels.append(p)


def row(title, y):
    global _id
    _id += 1
    panels.append({"id": _id, "type": "row", "title": title, "collapsed": False,
                   "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": []})


# ---- headline numbers ----
row("Service health", 0)
panel("stat", "Request rate", [(f"sum(rate(http_requests_total{{{API}}}[$__rate_interval]))", "")],
      0, 1, 5, 4, unit="reqps", decimals=2)
panel("stat", "p95 latency",
      [(f"histogram_quantile(0.95, sum by (le) (rate(http_request_duration_highr_seconds_bucket{{{NS}}}[$__rate_interval])))", "")],
      5, 1, 5, 4, unit="s", decimals=3,
      steps=[{"color": "green", "value": None}, {"color": "orange", "value": 0.3}, {"color": "red", "value": 0.5}])
panel("stat", "5xx error rate",
      [(f'(sum(rate(http_requests_total{{{API}, status=~"5.."}}[$__rate_interval])) or vector(0)) '
        f"/ clamp_min(sum(rate(http_requests_total{{{API}}}[$__rate_interval])), 1e-9)", "")],
      10, 1, 5, 4, unit="percentunit", decimals=2,
      steps=[{"color": "green", "value": None}, {"color": "orange", "value": 0.01}, {"color": "red", "value": 0.05}])
panel("stat", "Backend pods up", [(f'sum(up{{{NS}, service=~".*backend"}})', "")], 15, 1, 4, 4,
      steps=[{"color": "red", "value": None}, {"color": "orange", "value": 1}, {"color": "green", "value": 2}])
panel("stat", "Bookings (last 24h)",
      [(f"sum(increase(slotsync_appointments_created_total{{{NS}}}[24h]))", "")], 19, 1, 5, 4, decimals=0,
      steps=[{"color": "blue", "value": None}])

# ---- traffic ----
row("HTTP traffic", 5)
panel("timeseries", "Requests per second by endpoint",
      [(f"sum by (method, handler) (rate(http_requests_total{{{API}}}[$__rate_interval]))", "{{method}} {{handler}}")],
      0, 6, 12, 8, unit="reqps")
panel("timeseries", "Latency percentiles",
      [(f"histogram_quantile({q}, sum by (le) (rate(http_request_duration_highr_seconds_bucket{{{NS}}}[$__rate_interval])))", f"p{int(q*100)}")
       for q in (0.5, 0.95, 0.99)],
      12, 6, 12, 8, unit="s")
panel("timeseries", "Responses by status code",
      [(f"sum by (status) (rate(http_requests_total{{{API}}}[$__rate_interval]))", "{{status}}")],
      0, 14, 12, 8, unit="reqps", stack="normal")
panel("timeseries", "p95 latency by endpoint",
      [(f"histogram_quantile(0.95, sum by (le, handler) (rate(http_request_duration_seconds_bucket{{{API}}}[$__rate_interval])))", "{{handler}}")],
      12, 14, 12, 8, unit="s")

# ---- business ----
row("Bookings", 22)
panel("timeseries", "Bookings created by service",
      [(f"sum by (service) (increase(slotsync_appointments_created_total{{{NS}}}[$__rate_interval]))", "{{service}}")],
      0, 23, 8, 8, stack="normal", decimals=0)
panel("timeseries", "Status changes",
      [(f"sum by (status) (increase(slotsync_appointment_status_changes_total{{{NS}}}[$__rate_interval]))", "{{status}}")],
      8, 23, 8, 8, stack="normal", decimals=0)
panel("timeseries", "Double-booking attempts rejected (409)",
      [(f"sum(increase(slotsync_booking_conflicts_total{{{NS}}}[$__rate_interval]))", "conflicts")],
      16, 23, 8, 8, decimals=0)

# ---- capacity ----
row("Capacity & autoscaling", 31)
panel("timeseries", "Backend CPU by pod",
      [(f'sum by (pod) (rate(container_cpu_usage_seconds_total{{{NS}, container="backend"}}[$__rate_interval]))', "{{pod}}")],
      0, 32, 8, 8, unit="cores")
panel("timeseries", "Backend memory by pod",
      [(f'sum by (pod) (container_memory_working_set_bytes{{{NS}, container="backend"}})', "{{pod}}")],
      8, 32, 8, 8, unit="bytes")
panel("timeseries", "HPA replicas (backend)",
      [(f'kube_horizontalpodautoscaler_status_current_replicas{{{NS}, horizontalpodautoscaler=~".*backend"}}', "current"),
       (f'kube_horizontalpodautoscaler_status_desired_replicas{{{NS}, horizontalpodautoscaler=~".*backend"}}', "desired"),
       (f'kube_horizontalpodautoscaler_spec_max_replicas{{{NS}, horizontalpodautoscaler=~".*backend"}}', "max")],
      16, 32, 8, 8, decimals=0)

dashboard = {
    "uid": "slotsync-overview",
    "title": "SlotSync / API overview",
    "description": "Traffic, latency, errors, bookings and autoscaling for the SlotSync appointment platform",
    "tags": ["slotsync", "fastapi"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"},
    "editable": True,
    "graphTooltip": 1,
    "templating": {
        "list": [
            {"name": "datasource", "type": "datasource", "query": "prometheus", "label": "Data source",
             "current": {"text": "Prometheus", "value": "prometheus"}},
            {"name": "namespace", "type": "custom", "label": "Namespace", "query": "slotsync",
             "current": {"text": "slotsync", "value": "slotsync"},
             "options": [{"text": "slotsync", "value": "slotsync", "selected": True}]},
        ]
    },
    "panels": panels,
}

out = Path(__file__).resolve().parent.parent / "helm/slotsync/dashboards/slotsync.json"
out.write_text(json.dumps(dashboard, indent=2) + "\n")
print(f"wrote {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out} ({len(panels)} panels)")
