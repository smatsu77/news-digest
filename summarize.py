from __future__ import annotations
import json
import logging
import time
from typing import List
import anthropic
from config import RawArticle, Article, classify_category, get_env

logger = logging.getLogger(__name__)

def _build_prompt(raw: RawArticle) -> str:
    state_note = (
        "\n WARNING: This is state-controlled media. In summaries, frame claims as "
        "'[source] reports that ...' rather than neutral fact."
    ) if raw.state_media else ""
    return (
        f"You are a bilingual news editor. Output ONLY valid JSON, no markdown fences.\n\n"
        f"Source: {raw.source} (tier: {raw.tier}){state_note}\n"
        f"Title: {raw.title}\n"
        f"Excerpt: {raw.raw_summary[:600]}\n\n"
        f"Required JSON:\n"
        f'{{"title_en":"<clean English title, max 120 chars>",'
        f'"summary_en":"<2-3 sentence English summary>",'
        f'"title_ja":"<Japanese title>",'
        f'"summary_ja":"<2-3 sentence Japanese summary>"}}'
    )

def summarize_articles(
    raw_articles: List[RawArticle],
    rate_limit_delay: float = 0.3,
) -> List[Article]:
    client = anthropic.Anthropic(api_key=get_env("ANTHROPIC_API_KEY"))
    articles: List[Article] = []

    for raw in raw_articles:
        if not raw.title:
            continue
        category = classify_category(raw.title, raw.raw_summary)
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                messages=[{"role": "user", "content": _build_prompt(raw)}],
            )
            data = json.loads(response.content[0].text)
            articles.append(Article(
                title_en=data["title_en"],
                title_ja=data["title_ja"],
                summary_en=data["summary_en"],
                summary_ja=data["summary_ja"],
                source=raw.source,
                tier=raw.tier,
                link=raw.link,
                state_media=raw.state_media,
                category=category,
                published=raw.published,
            ))
        except Exception as exc:
            logger.warning(f"Summarize failed for '{raw.title[:60]}': {exc}")
            articles.append(Article(
                title_en=raw.title,
                title_ja=raw.title,
                summary_en=raw.raw_summary[:300],
                summary_ja=raw.raw_summary[:300],
                source=raw.source,
                tier=raw.tier,
                link=raw.link,
                state_media=raw.state_media,
                category=category,
                published=raw.published,
            ))
        time.sleep(rate_limit_delay)

    return articles
