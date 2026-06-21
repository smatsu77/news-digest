from __future__ import annotations
import html as _html
import json
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
      --accent:#c8a96e;--danger:#e05555;--tab-bg:#1a1a1a;--tab-active:#c8a96e}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:"Hiragino Kaku Gothic Pro","Yu Gothic","Meiryo",sans-serif;
      max-width:640px;margin:0 auto;min-height:100vh}}
/* Header */
.header{{background:#111;padding:.75rem 1rem;border-bottom:2px solid var(--accent);
         position:sticky;top:0;z-index:100}}
.header h1{{font-size:1.1rem;color:var(--accent);letter-spacing:.05em}}
.header .date{{font-size:.7rem;color:var(--muted);margin-top:.1rem}}
/* Tabs */
.tabs{{display:flex;overflow-x:auto;background:var(--tab-bg);
       border-bottom:1px solid var(--border);scrollbar-width:none}}
.tabs::-webkit-scrollbar{{display:none}}
.tab{{flex:none;padding:.6rem 1rem;font-size:.85rem;color:var(--muted);
      border:none;background:none;cursor:pointer;border-bottom:2px solid transparent;
      white-space:nowrap}}
.tab.active{{color:var(--accent);border-bottom-color:var(--accent);font-weight:bold}}
/* List view */
#list-view{{padding:.5rem 0}}
.art-item{{display:flex;align-items:baseline;gap:.4rem;padding:.6rem 1rem;
           border-bottom:1px solid var(--border);cursor:pointer}}
.art-item:active{{background:var(--card)}}
.art-item.state .art-hed{{color:#ff9999}}
.bullet{{color:var(--accent);flex-shrink:0;font-size:.9rem}}
.bullet.st{{color:var(--danger)}}
.art-hed{{font-size:.88rem;line-height:1.4;flex:1}}
.art-src{{font-size:.7rem;color:var(--muted);flex-shrink:0}}
/* Detail view */
#detail-view{{display:none;padding:1rem}}
.back-btn{{display:inline-flex;align-items:center;gap:.3rem;color:var(--accent);
           font-size:.85rem;cursor:pointer;margin-bottom:1rem;padding:.3rem 0}}
.orig-link{{display:block;color:var(--accent);font-size:.8rem;margin-bottom:1rem;
            padding:.5rem .75rem;border:1px solid var(--accent);border-radius:4px;
            text-decoration:none;word-break:break-all}}
.orig-link:hover{{background:rgba(200,169,110,.1)}}
.state-badge{{color:var(--danger);font-size:.75rem;font-weight:bold;margin-bottom:.5rem}}
.detail-title-ja{{font-size:1rem;font-weight:bold;line-height:1.5;margin-bottom:.75rem}}
.detail-summ-ja{{font-size:.88rem;line-height:1.7;color:#ccc;margin-bottom:1.25rem}}
.divider{{border:none;border-top:1px solid var(--border);margin:1rem 0}}
.detail-title-en{{font-size:.9rem;font-weight:bold;line-height:1.4;color:#bbb;margin-bottom:.5rem}}
.detail-summ-en{{font-size:.82rem;line-height:1.6;color:var(--muted)}}
.detail-source{{font-size:.72rem;color:var(--muted);margin-top:.75rem}}
/* Footer */
.footer{{font-size:.68rem;color:var(--muted);text-align:center;padding:1.5rem 1rem;
         border-top:1px solid var(--border)}}
</style>
</head>
<body>
<div class="header">
  <h1>Morning Read</h1>
  <div class="date">{date}</div>
</div>
<div class="tabs" id="tabs"></div>
<div id="list-view"></div>
<div id="detail-view">
  <div class="back-btn" onclick="backToList()">&#8592; 戻る</div>
  <a class="orig-link" id="d-link" href="#" target="_blank" rel="noopener">&#128279; 元記事を開く</a>
  <div class="state-badge" id="d-state" style="display:none">⚠ 国営系メディア — 主張は中立的事実として扱わない</div>
  <div class="detail-title-ja" id="d-title-ja"></div>
  <div class="detail-summ-ja" id="d-summ-ja"></div>
  <hr class="divider">
  <div class="detail-title-en" id="d-title-en"></div>
  <div class="detail-summ-en" id="d-summ-en"></div>
  <div class="detail-source" id="d-source"></div>
</div>
<div class="footer" id="footer"></div>
<script>
const CATS = ["全て","政治","経済","IT","社会","オピニオン"];
const DATA = {data_json};
let curCat = "全て";

function esc(s){{return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}}

function renderTabs(){{
  const el=document.getElementById("tabs");
  el.innerHTML=CATS.map(c=>`<button class="tab${{c===curCat?" active":""}}" onclick="setCat('${{c}}')">${{c}}</button>`).join("");
}}

function filteredArts(){{
  return curCat==="全て"?DATA:DATA.filter(a=>a.category===curCat);
}}

function renderList(){{
  const arts=filteredArts();
  const el=document.getElementById("list-view");
  if(!arts.length){{el.innerHTML='<p style="padding:1rem;color:var(--muted)">記事なし</p>';return;}}
  el.innerHTML=arts.map((a,i)=>{{
    const sm=a.state_media;
    return `<div class="art-item${{sm?" state":""}}" onclick="showDetail(${{i}})">
      <span class="bullet${{sm?" st":""}}">${{sm?"[!]":"•"}}</span>
      <span class="art-hed">${{esc(a.title_ja)}}</span>
      <span class="art-src">${{esc(a.source)}}</span>
    </div>`;
  }}).join("");
}}

function setCat(cat){{curCat=cat;renderTabs();renderList();document.getElementById("list-view").style.display="block";document.getElementById("detail-view").style.display="none";}}

function showDetail(idx){{
  const a=filteredArts()[idx];
  document.getElementById("d-link").href=a.link;
  const sb=document.getElementById("d-state");
  sb.style.display=a.state_media?"block":"none";
  document.getElementById("d-title-ja").textContent=a.title_ja;
  document.getElementById("d-summ-ja").textContent=a.summary_ja;
  document.getElementById("d-title-en").textContent=a.title_en;
  document.getElementById("d-summ-en").textContent=a.summary_en;
  document.getElementById("d-source").textContent=a.source+" / "+a.tier;
  document.getElementById("list-view").style.display="none";
  document.getElementById("detail-view").style.display="block";
  window.scrollTo(0,0);
}}

function backToList(){{document.getElementById("list-view").style.display="block";document.getElementById("detail-view").style.display="none";window.scrollTo(0,0);}}

document.getElementById("footer").textContent="Generated {ts} JST";
renderTabs();renderList();
</script>
</body>
</html>"""

def _safe_json(articles: List[Article]) -> str:
    data = [
        {
            "title_ja": a.title_ja,
            "title_en": a.title_en,
            "summary_ja": a.summary_ja,
            "summary_en": a.summary_en,
            "source": a.source,
            "tier": a.tier,
            "link": a.link,
            "state_media": a.state_media,
            "category": a.category,
        }
        for a in articles
    ]
    # Escape </script> to prevent XSS via JSON injection
    return json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>")

def render_html(articles: List[Article], date_str: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return _TEMPLATE.format(
        date=date_str,
        data_json=_safe_json(articles),
        ts=ts,
    )

def write_html(articles: List[Article], docs_dir: Path = Path("docs")) -> tuple[Path, Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    content = render_html(articles, date_str)
    dated = docs_dir / f"morning-read-{date_str}.html"
    latest = docs_dir / "latest.html"
    dated.write_text(content, encoding="utf-8")
    latest.write_text(content, encoding="utf-8")
    return dated, latest
