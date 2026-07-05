from __future__ import annotations
import logging
import re
from typing import List
import feedparser
from config import Source, RawArticle, SOURCES

def _strip_html(text: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    return re.sub(r'\s+', ' ', text).strip()

def _fetch_full_text(url: str, timeout: int = 10) -> str:
    """Try to fetch full article body via trafilatura. Returns '' if blocked/paywalled."""
    if not url:
        return ""
    try:
        import trafilatura
        html = trafilatura.fetch_url(url, no_ssl=False)
        if not html:
            return ""
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if not text or len(text) < 100:
            return ""
        return text[:5000]
    except Exception:
        return ""

logger = logging.getLogger(__name__)
MAX_ITEMS_PER_SOURCE = 3

def fetch_source(source: Source) -> List[RawArticle]:
    """Fetch one RSS source. Returns [] on any failure (graceful skip)."""
    if not source.url:          # AFP and any future no-RSS source
        logger.info(f"[{source.name}] No RSS URL configured, skipping")
        return []
    try:
        feed = feedparser.parse(source.url)
        if not feed.entries:
            logger.warning(f"[{source.name}] No entries (bozo={feed.bozo})")
            return []
        articles = []
        for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
            title = entry.get("title", "").strip()
            if not title:
                continue
            link = entry.get("link", "")
            full_text = _fetch_full_text(link) if source.fetch_full_text else ""
            if full_text:
                logger.info(f"[{source.name}] Full text fetched ({len(full_text)} chars): {title[:40]}")
            articles.append(RawArticle(
                title=title,
                link=link,
                source=source.name,
                tier=source.tier,
                state_media=source.state_media,
                raw_summary=_strip_html((entry.get("summary") or entry.get("description") or ""))[:1000],
                full_text=full_text,
                published=entry.get("published", ""),
            ))
        return articles
    except Exception as exc:
        logger.warning(f"[{source.name}] Fetch error: {exc}")
        return []

def fetch_all(sources: List[Source] = SOURCES) -> List[RawArticle]:
    results: List[RawArticle] = []
    for source in sources:
        items = fetch_source(source)
        logger.info(f"[{source.name}] fetched {len(items)} items")
        results.extend(items)
    return results

if __name__ == "__main__":
    """CLI validation mode: python fetch.py"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("=== RSS URL Validation ===\n")
    ok, fail = [], []
    for source in SOURCES:
        items = fetch_source(source)
        flag = " [STATE MEDIA]" if source.state_media else ""
        if items:
            print(f"  [OK]  [{source.tier}] {source.name}{flag}: {len(items)} items")
            ok.append(source.name)
        elif not source.url:
            print(f"  [--]  [{source.tier}] {source.name}{flag}: no URL, skipped")
        else:
            print(f"  [NG]  [{source.tier}] {source.name}{flag}: FAILED")
            fail.append(source.name)
    print(f"\nResult: {len(ok)} OK / {len(fail)} FAILED")
    if fail:
        print(f"Failed sources: {fail}")
