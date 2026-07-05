from __future__ import annotations
import html as _html
import json
from datetime import datetime
from pathlib import Path
from typing import List
from config import Article, Comparison, TIERS, TIER_LABELS, CATEGORIES

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
/* Full text sections */
.section-label{{font-size:.78rem;color:var(--accent);font-weight:bold;
                letter-spacing:.05em;margin-bottom:.5rem;margin-top:.25rem}}
.detail-fulltext-en{{font-size:.82rem;line-height:1.8;color:var(--muted);
                     white-space:pre-wrap;word-break:break-word}}
.detail-translation{{font-size:.88rem;line-height:1.8;color:#ccc;
                     white-space:pre-wrap;word-break:break-word}}
/* Vocab */
.vocab-item{{margin-bottom:.75rem}}
.vocab-word{{font-weight:bold;color:var(--accent);font-size:.88rem;display:block}}
.vocab-def{{font-size:.82rem;color:#ccc;line-height:1.6}}
/* Focus section */
.focus-section{{background:var(--card);border:1px solid var(--accent);border-radius:6px;
               margin:.75rem 1rem;padding:1rem}}
.focus-label{{font-size:.7rem;color:var(--accent);font-weight:bold;letter-spacing:.1em;margin-bottom:.3rem}}
.focus-topic{{font-size:.95rem;font-weight:bold;line-height:1.4;margin-bottom:.75rem}}
.focus-analysis{{font-size:.82rem;line-height:1.7;color:#ccc;margin-bottom:.75rem}}
.cov-list{{display:flex;flex-direction:column;gap:.5rem}}
.cov-card{{background:#111;border-radius:4px;padding:.6rem .75rem;border-left:3px solid var(--accent)}}
.cov-card.state-media{{border-left-color:var(--danger)}}
.cov-header{{display:flex;align-items:center;gap:.4rem;margin-bottom:.2rem}}
.cov-region{{font-size:.65rem;color:var(--accent);font-weight:bold;background:rgba(200,169,110,.15);
             padding:.1rem .4rem;border-radius:3px}}
.cov-name{{font-size:.75rem;font-weight:bold;color:var(--text)}}
.cov-summary{{font-size:.78rem;color:#ccc;line-height:1.5;margin-bottom:.2rem}}
.cov-perspective{{font-size:.74rem;color:var(--muted);line-height:1.4;font-style:italic}}
.cov-link{{font-size:.7rem;color:var(--accent);text-decoration:none}}
/* Share */
.share-btn{{display:inline-flex;align-items:center;gap:.3rem;background:none;
           border:1px solid var(--accent);color:var(--accent);border-radius:4px;
           padding:.3rem .75rem;font-size:.78rem;cursor:pointer;margin-left:.75rem}}
.share-btn:active{{opacity:.7}}
.share-block{{background:var(--card);border:1px solid var(--border);border-radius:6px;
             padding:1rem;margin:.75rem 1rem}}
.share-title{{font-size:.85rem;font-weight:bold;color:var(--accent);margin-bottom:.4rem}}
.share-desc{{font-size:.78rem;color:var(--muted);margin-bottom:.5rem;line-height:1.5}}
.share-topic{{font-size:.8rem;color:#ccc;margin-bottom:.5rem}}
.share-topic code{{background:#111;padding:.1rem .4rem;border-radius:3px;
                   color:var(--accent);font-family:monospace}}
.share-link{{display:inline-block;font-size:.8rem;color:var(--accent);text-decoration:none}}
/* Footer */
.footer{{font-size:.68rem;color:var(--muted);text-align:center;padding:1.5rem 1rem;
         border-top:1px solid var(--border)}}
</style>
</head>
<body>
<div class="header">
  <h1>Morning Read</h1>
  <div style="display:flex;align-items:center;margin-top:.2rem">
    <div class="date">{date}</div>
    <button class="share-btn" onclick="shareUrl()">&#128279; 共有</button>
  </div>
</div>
{focus_block}
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
  <div id="d-fulltext-section" style="display:none">
    <hr class="divider">
    <div class="section-label">全文（英語）</div>
    <div class="detail-fulltext-en" id="d-fulltext-en"></div>
    <hr class="divider">
    <div class="section-label">日本語訳（全文）</div>
    <div class="detail-translation" id="d-translation-ja"></div>
  </div>
  <div id="d-vocab-section" style="display:none">
    <hr class="divider">
    <div class="section-label">難単語（TOEIC 800+）</div>
    <div id="d-vocab-list"></div>
  </div>
  <div class="detail-source" id="d-source"></div>
</div>
{ntfy_block}
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
  document.getElementById("d-state").style.display=a.state_media?"block":"none";
  document.getElementById("d-title-ja").textContent=a.title_ja;
  document.getElementById("d-summ-ja").textContent=a.summary_ja;
  document.getElementById("d-title-en").textContent=a.title_en;
  document.getElementById("d-summ-en").textContent=a.summary_en;
  const fts=document.getElementById("d-fulltext-section");
  if(a.full_text){{
    document.getElementById("d-fulltext-en").textContent=a.full_text;
    document.getElementById("d-translation-ja").textContent=a.translation_ja||"";
    fts.style.display="block";
  }}else{{fts.style.display="none";}}
  const vs=document.getElementById("d-vocab-section");
  if(a.vocab&&a.vocab.length){{
    document.getElementById("d-vocab-list").innerHTML=a.vocab.map(v=>
      `<div class="vocab-item"><span class="vocab-word">${{esc(v.word)}}</span><span class="vocab-def">${{esc(v.definition)}}</span></div>`
    ).join("");
    vs.style.display="block";
  }}else{{vs.style.display="none";}}
  document.getElementById("d-source").textContent=a.source+" / "+a.tier;
  document.getElementById("list-view").style.display="none";
  document.getElementById("detail-view").style.display="block";
  window.scrollTo(0,0);
}}

function backToList(){{document.getElementById("list-view").style.display="block";document.getElementById("detail-view").style.display="none";window.scrollTo(0,0);}}

function shareUrl(){{
  const url=location.href;
  if(navigator.share){{navigator.share({{title:"Morning Read",url:url}});}}
  else{{navigator.clipboard.writeText(url).then(()=>alert("URLをコピーしました")).catch(()=>prompt("このURLをコピーしてください:",url));}}
}}

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
            "full_text": a.full_text,
            "translation_ja": a.translation_ja,
            "vocab": a.vocab,
        }
        for a in articles
    ]
    # Escape </script> to prevent XSS via JSON injection
    return json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>")

def _build_focus_block(comparison: "Comparison | None") -> str:
    if not comparison:
        return ""
    cards = []
    for c in comparison.coverages:
        state_cls = " state-media" if c.state_media else ""
        state_badge = ' <span style="color:var(--danger);font-size:.65rem">[国営]</span>' if c.state_media else ""
        cards.append(
            f'<div class="cov-card{state_cls}">'
            f'<div class="cov-header">'
            f'<span class="cov-region">{_html.escape(c.region)}</span>'
            f'<span class="cov-name">{_html.escape(c.name)}{state_badge}</span>'
            f'</div>'
            f'<div class="cov-summary">{_html.escape(c.summary_ja)}</div>'
            f'<div class="cov-perspective">{_html.escape(c.perspective_ja)}</div>'
            f'<a class="cov-link" href="{_html.escape(c.link)}" target="_blank" rel="noopener">元記事 →</a>'
            f'</div>'
        )
    return (
        f'<div class="focus-section">'
        f'<div class="focus-label">&#127919; 今日の焦点 — 5社の報道比較</div>'
        f'<div class="focus-topic">{_html.escape(comparison.topic_ja)}</div>'
        f'<div class="focus-analysis">{_html.escape(comparison.analysis_ja)}</div>'
        f'<div class="cov-list">{"".join(cards)}</div>'
        f'</div>'
    )


def render_html(articles: List[Article], date_str: str, ntfy_topic: str = "",
                comparison: "Comparison | None" = None) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    ntfy_block = ""
    if ntfy_topic:
        ntfy_block = (
            f'<div class="share-block">'
            f'<div class="share-title">&#128276; プッシュ通知を受け取る</div>'
            f'<div class="share-desc">ntfy アプリをインストールしてトピックを購読すると、毎日11時・22時に通知が届きます。</div>'
            f'<div class="share-topic">トピック名: <code>{_html.escape(ntfy_topic)}</code></div>'
            f'<a class="share-link" href="https://ntfy.sh/{_html.escape(ntfy_topic)}" target="_blank" rel="noopener">'
            f'&#128279; ntfy.sh で購読する</a>'
            f'</div>'
        )
    return _TEMPLATE.format(
        date=date_str,
        data_json=_safe_json(articles),
        ts=ts,
        ntfy_block=ntfy_block,
        focus_block=_build_focus_block(comparison),
    )

def write_html(articles: List[Article], docs_dir: Path = Path("docs"), ntfy_topic: str = "",
               comparison: "Comparison | None" = None) -> tuple[Path, Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    content = render_html(articles, date_str, ntfy_topic=ntfy_topic, comparison=comparison)
    dated = docs_dir / f"morning-read-{date_str}.html"
    latest = docs_dir / "latest.html"
    dated.write_text(content, encoding="utf-8")
    latest.write_text(content, encoding="utf-8")
    return dated, latest
