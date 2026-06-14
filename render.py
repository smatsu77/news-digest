from __future__ import annotations
import html as _html
from datetime import datetime
from pathlib import Path
from typing import List
from config import Article, TIERS, TIER_LABELS, CATEGORIES

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Read — {date}</title>
<style>
:root{{--bg:#0e0e0e;--card:#1a1a1a;--border:#2e2e2e;--text:#ddd;--muted:#777;
      --accent:#c8a96e;--danger:#e05555}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);
      font-family:"Georgia","Times New Roman",serif;
      max-width:960px;margin:0 auto;padding:1.5rem 1rem}}
h1{{font-size:2rem;color:var(--accent);border-bottom:2px solid var(--accent);
    padding-bottom:.5rem;margin-bottom:2rem;letter-spacing:.05em}}
h2{{font-size:1.15rem;color:var(--accent);margin:1.8rem 0 .6rem;
    border-left:4px solid var(--accent);padding-left:.6rem;text-transform:uppercase;
    letter-spacing:.08em}}
h3{{font-size:.8rem;color:var(--muted);text-transform:uppercase;
    letter-spacing:.12em;margin:.8rem 0 .3rem}}
.art{{background:var(--card);border:1px solid var(--border);border-radius:3px;
      padding:.8rem 1rem;margin:.4rem 0}}
.art.sm{{border-left:4px solid var(--danger)}}
.art-title a{{color:var(--text);text-decoration:none;font-weight:bold;
              line-height:1.4}}
.art-title a:hover{{color:var(--accent);text-decoration:underline}}
.art-title-ja{{color:#999;font-style:italic;font-size:.85rem;margin-top:.2rem}}
.badge{{color:var(--danger);font-size:.75rem;font-weight:bold;margin-right:.3rem}}
.src{{font-size:.72rem;color:var(--muted);margin:.2rem 0 .5rem}}
.summ{{font-size:.82rem;line-height:1.6;color:#c0c0c0}}
.summ-ja{{color:#999;font-style:italic;margin-top:.3rem}}
.region{{margin-bottom:2rem}}
.ts{{font-size:.7rem;color:var(--muted);text-align:right;margin-top:2.5rem;
     border-top:1px solid var(--border);padding-top:.5rem}}
</style>
</head>
<body>
<h1>Morning Read &mdash; {date}</h1>
{body}
<p class="ts">Generated {ts} JST &bull; news-digest</p>
</body>
</html>"""

def _e(s: str) -> str:
    return _html.escape(s)

def _article_html(art: Article) -> str:
    cls = " sm" if art.state_media else ""
    badge = '<span class="badge">⚠国営系</span>' if art.state_media else ""
    return (
        f'<div class="art{cls}">'
        f'<div class="art-title">{badge}'
        f'<a href="{_e(art.link)}" target="_blank" rel="noopener noreferrer">'
        f'{_e(art.title_en)}</a></div>'
        f'<div class="art-title-ja">{_e(art.title_ja)}</div>'
        f'<div class="src">{_e(art.source)}</div>'
        f'<div class="summ">{_e(art.summary_en)}</div>'
        f'<div class="summ summ-ja">{_e(art.summary_ja)}</div>'
        f'</div>'
    )

def render_html(articles: List[Article], date_str: str) -> str:
    by_tier: dict[str, dict[str, list[Article]]] = {
        t: {c: [] for c in CATEGORIES} for t in TIERS
    }
    for art in articles:
        if art.tier in by_tier and art.category in by_tier[art.tier]:
            by_tier[art.tier][art.category].append(art)

    parts: list[str] = []
    for tier in TIERS:
        cats = by_tier[tier]
        if not any(cats.values()):
            continue
        label = TIER_LABELS.get(tier, tier)
        parts.append(f'<div class="region"><h2>{_e(label)}</h2>')
        for cat in CATEGORIES:
            arts = cats[cat]
            if not arts:
                continue
            parts.append(f'<h3>{_e(cat)}</h3>')
            parts.extend(_article_html(a) for a in arts)
        parts.append("</div>")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return _TEMPLATE.format(date=date_str, body="\n".join(parts), ts=ts)

def write_html(articles: List[Article], docs_dir: Path = Path("docs")) -> tuple[Path, Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    content = render_html(articles, date_str)
    dated = docs_dir / f"morning-read-{date_str}.html"
    latest = docs_dir / "latest.html"
    dated.write_text(content, encoding="utf-8")
    latest.write_text(content, encoding="utf-8")
    return dated, latest
