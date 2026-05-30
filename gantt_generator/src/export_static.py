import plotly.graph_objects as go


def export_plotly_figure(fig: go.Figure, fmt: str = "png") -> bytes:
    plot_json = fig.to_json()

    btn_css = "padding:10px 20px;font-size:14px;border:none;border-radius:6px;cursor:pointer;font-weight:500;margin-right:8px"

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>Gantt Chart Export</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{{font-family:Arial,sans-serif;margin:0;padding:16px;background:#f5f5f5}}
.toolbar{{background:#fff;border-radius:8px;padding:16px 20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.1);display:flex;align-items:center;gap:12px}}
.toolbar span{{font-weight:600;color:#333}}
.btn-png{{background:#1f77b4;color:#fff}}
.btn-svg{{background:#2ca02c;color:#fff}}
.btn-jpeg{{background:#ff7f0e;color:#fff}}
.btn-pdf{{background:#d62728;color:#fff}}
#chart{{background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
</style>
</head>
<body>
<div class="toolbar">
<span>Export:</span>
<button class="btn-png" style="{btn_css}" onclick="doExp('png')">Download PNG</button>
<button class="btn-svg" style="{btn_css}" onclick="doExp('svg')">Download SVG</button>
<button class="btn-jpeg" style="{btn_css}" onclick="doExp('jpeg')">Download JPEG</button>
<button class="btn-pdf" style="{btn_css}" onclick="window.print()">Save as PDF</button>
</div>
<div id="chart"></div>
<script>
var gd={plot_json};
var L=gd.layout||{{}};
L.autosize=true;
L.width=null;
if(!L.height||L.height<500)L.height=500;
Plotly.newPlot('chart',gd.data,L,{{responsive:true,displayModeBar:true}});
function doExp(f){{Plotly.downloadImage('chart',{{format:f,width:1600,height:900,filename:'gantt-chart'}});}}
</script>
</body>
</html>"""
    return html.encode("utf-8")