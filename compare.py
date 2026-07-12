from __future__ import annotations
import json
import logging
import urllib.parse
from typing import List, Optional

import feedparser
import anthropic

from config import Article, Comparison, Coverage, get_env
from fetch import _fetch_full_text, _strip_html

logger = logging.getLogger(__name__)

# 地域ごとに1社ずつ、バランスよく選定
REGIONAL_OUTLETS = [
    {"region": "北米",       "name": "AP News",    "site": "apnews.com",          "state": False},
    {"region": "欧州",       "name": "BBC",         "site": "bbc.com",             "state": False},
    {"region": "中東",       "name": "Al Jazeera", "site": "aljazeera.com",       "state": False},
    {"region": "南アジア",   "name": "The Hindu",  "site": "thehindu.com",        "state": False},
    {"region": "東アジア",   "name": "Xinhua",     "site": "english.news.cn",     "state": True},
]

MIN_COVERAGES = 2  # 最低2社揃わなければスキップ


def _pick_top_story(articles: List[Article]) -> Optional[str]:
    """Wireサービス（AP/Reuters）の先頭記事から今日のトップニュースを英語クエリで返す。"""
    wire_arts = [a for a in articles if a.tier == "wire" and a.title_en]
    if not wire_arts:
        wire_arts = [a for a in articles if a.title_en]
    if not wire_arts:
        return None
    # 先頭3件をClaudeに渡して最も国際的な1件を選ばせる
    client = anthropic.Anthropic(api_key=get_env("ANTHROPIC_API_KEY"))
    candidates = "\n".join(f"- {a.title_en}" for a in wire_arts[:5])
    prompt = (
        "From these news headlines, pick the ONE story most likely to be reported globally "
        "across multiple regions (Americas, Europe, Middle East, Asia). "
        "Return ONLY a short English search query (5-8 words, no quotes) for that story.\n\n"
        f"Headlines:\n{candidates}"
    )
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as exc:
        logger.warning(f"[compare] top story pick failed: {exc}")
        return wire_arts[0].title_en[:80] if wire_arts else None


def _fetch_outlet_coverage(query: str, outlet: dict) -> Optional[dict]:
    """Google News でクエリ×特定サイトを検索し、記事タイトル・全文・リンクを返す。"""
    # フル検索 → 短縮フォールバック（3語）の順で試みる
    short_query = " ".join(query.split()[:3])
    candidates = [query, short_query] if query != short_query else [query]

    entry = None
    for q in candidates:
        encoded = urllib.parse.quote(f"{q} site:{outlet['site']}")
        rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                entry = feed.entries[0]
                break
        except Exception as exc:
            logger.warning(f"[compare] RSS fetch failed for {outlet['name']}: {exc}")

    if not entry:
        logger.info(f"[compare] no results for {outlet['name']}")
        return None

    try:
        link = entry.get("link", "")
        full_text = _fetch_full_text(link)
        summary = _strip_html(entry.get("summary", ""))[:800]
        title = entry.get("title", "").strip()
        # コンテンツ: 全文 > RSS要約 > タイトルのみ（最低限の情報で続行）
        content = full_text or summary or title
        if not content:
            return None
        return {
            "region": outlet["region"],
            "name": outlet["name"],
            "title": title,
            "link": link,
            "content": content,
            "state_media": outlet["state"],
        }
    except Exception as exc:
        logger.warning(f"[compare] fetch failed for {outlet['name']}: {exc}")
        return None


def _extract_json(text: str) -> str:
    """マークダウンのコードブロックを除去してJSONを抽出する。"""
    text = text.strip()
    # ```json ... ``` または ``` ... ``` を除去
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    # 先頭の { から末尾の } まで抽出
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text


def _generate_comparison(query: str, raw_coverages: List[dict]) -> Optional[Comparison]:
    """各社の記事をClaudeに渡し、報道差異を日本語でまとめる。"""
    client = anthropic.Anthropic(api_key=get_env("ANTHROPIC_API_KEY"))

    sections = []
    for c in raw_coverages:
        state_note = "（国営メディア）" if c["state_media"] else ""
        sections.append(
            f"[{c['name']} / {c['region']}{state_note}]\n"
            f"Title: {c['title']}\n"
            f"Content: {c['content'][:1000]}"  # 1500→1000に削減してトークン節約
        )

    prompt = (
        "You are a media analyst. Compare how these regional news outlets cover the same story.\n"
        "Output ONLY valid JSON with NO markdown fences, NO explanation outside the JSON.\n\n"
        f"Story topic: {query}\n\n"
        + "\n\n---\n\n".join(sections)
        + "\n\nRequired JSON format:\n"
        '{"topic_en":"<story topic in English, max 100 chars>",'
        '"topic_ja":"<story topic in Japanese>",'
        '"analysis_ja":"<300字程度で各社の報道差異・強調点・視点の違いを比較分析>",'
        '"coverages":['
        '{"region":"<地域>","name":"<outlet name>","summary_ja":"<その社の報道を2文で要約>","perspective_ja":"<その社特有の視点を1文で>"}'
        "]}"
    )

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = resp.content[0].text
        logger.debug(f"[compare] raw response (first 200): {raw_text[:200]}")
        cleaned = _extract_json(raw_text)
        data = json.loads(cleaned)
        coverages = []
        for i, c in enumerate(data.get("coverages", [])):
            raw = raw_coverages[i] if i < len(raw_coverages) else {}
            coverages.append(Coverage(
                region=c.get("region", raw.get("region", "")),
                name=c.get("name", raw.get("name", "")),
                title=raw.get("title", ""),
                link=raw.get("link", ""),
                summary_ja=c.get("summary_ja", ""),
                perspective_ja=c.get("perspective_ja", ""),
                state_media=raw.get("state_media", False),
            ))
        return Comparison(
            topic_en=data["topic_en"],
            topic_ja=data["topic_ja"],
            analysis_ja=data["analysis_ja"],
            coverages=coverages,
        )
    except Exception as exc:
        logger.warning(f"[compare] generation failed: {exc}")
        return None


def build_comparison(articles: List[Article]) -> Optional[Comparison]:
    """メインパイプラインから呼ぶエントリーポイント。失敗時はNoneを返す。"""
    logger.info("[compare] Picking top story...")
    query = _pick_top_story(articles)
    if not query:
        logger.warning("[compare] Could not determine top story")
        return None
    logger.info(f"[compare] Top story query: {query}")

    raw_coverages = []
    for outlet in REGIONAL_OUTLETS:
        cov = _fetch_outlet_coverage(query, outlet)
        if cov:
            raw_coverages.append(cov)
            logger.info(f"[compare] Got coverage from {outlet['name']}")
        else:
            logger.info(f"[compare] No coverage from {outlet['name']}")

    if len(raw_coverages) < MIN_COVERAGES:
        logger.warning(f"[compare] Only {len(raw_coverages)} coverages found, skipping")
        return None

    return _generate_comparison(query, raw_coverages)
