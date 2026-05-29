"""
Inline CSS and static assets for the Phase 14 dashboard.
No external CDN. No remote JS/CSS.
"""

INLINE_CSS = """
:root {
  --bg: #f5f7fa;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --muted: #6b7280;
  --accent: #2563eb;
  --accent-light: #dbeafe;
  --danger: #dc2626;
  --danger-bg: #fee2e2;
  --success: #16a34a;
  --success-bg: #dcfce7;
  --warning: #ca8a04;
  --warning-bg: #fef9c3;
  --border: #e5e7eb;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }
.disclaimer {
  background: var(--danger-bg);
  color: var(--danger);
  border: 1px solid var(--danger);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  font-weight: 600;
  text-align: center;
}
.nav {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border);
}
.nav a {
  text-decoration: none;
  color: var(--accent);
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
}
.nav a:hover { background: var(--accent-light); }
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}
.card h2 { margin-top: 0; font-size: 1.25rem; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}
.stat {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}
.stat .number { font-size: 2rem; font-weight: 700; color: var(--accent); }
.stat .label { color: var(--muted); font-size: 0.875rem; margin-top: 4px; }
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}
th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
}
th { background: var(--accent-light); color: var(--accent); font-weight: 600; }
tr:hover { background: #f9fafb; }
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-ok { background: var(--success-bg); color: var(--success); }
.badge-warn { background: var(--warning-bg); color: var(--warning); }
.badge-err { background: var(--danger-bg); color: var(--danger); }
pre {
  background: #f3f4f6;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.875rem;
}
.code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875rem;
}
.footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.875rem;
  text-align: center;
}
a { color: var(--accent); }
.small { font-size: 0.875rem; color: var(--muted); }
"""


def wrap_html(title: str, body_content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Quant_Agent Dashboard</title>
<style>{INLINE_CSS}</style>
</head>
<body>
<div class="container">
  <div class="disclaimer">
    PAPER-ONLY / DATA-ONLY. No live trading. No order submission. No broker execution.
  </div>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/datasets">Datasets</a>
    <a href="/experiments/configs">Experiment Configs</a>
    <a href="/experiments/history">Experiment History</a>
    <a href="/dashboard/latest">Latest Dashboard JSON</a>
    <a href="/reports">Reports</a>
    <a href="/health">Health (JSON)</a>
  </div>
  {body_content}
  <div class="footer">
    Quant_Agent Local Dashboard &mdash; Phase 14 &mdash; Research use only.
  </div>
</div>
</body>
</html>
"""
