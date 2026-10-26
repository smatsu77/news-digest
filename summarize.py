from __future__ import annotations
import json
import logging
import time
from typing import List
import anthropic
from config import RawArticle, Article, classify_category, get_env

logger = logging.getLogger(__name__)

def _extract_json(text: str) -> str:
    """マークダウンのコードブロックを除去してJSONを抽出する。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text

def _build_prompt(raw: RawArticle) -> str:
    state_note = (
        "\n WARNING: This is state-controlled media. Frame claims as "
        "'[source] reports that ...' rather than neutral fact."
    ) if raw.state_media else ""
    opinion_note = (
        "\n NOTE: This is an opinion/editorial piece. Summarize the author's main argument."
    ) if raw.tier == "opinion" else ""

    if raw.full_text:
        content = raw.full_text[:2500]
        return (
            f"You are a bilingual news editor. Output ONLY valid JSON, no markdown fences.\n\n"
            f"Source: {raw.source}{state_note}{opinion_note}\n"
            f"Title: {raw.title}\n"
            f"Article:\n{content}\n\n"
            f"Required JSON:\n"
            f'{{"title_ja":"<Japanese title>",'
            f'"summary_ja":"<2-3 sentence Japanese summary>",'
            f'"vocab":[{{"word":"<English word>","definition":"<Japanese explanation, 1-2 sentences>"}}]}}\n\n'
            f"For vocab: extract 3-5 TOEIC 800+ level words. Do NOT include common words."
        )
    else:
        return (
            f"You are a bilingual news editor. Output ONLY valid JSON, no markdown fences.\n\n"
            f"Source: {raw.source}{state_note}{opinion_note}\n"
            f"Title: {raw.title}\n"
            f"Excerpt: {raw.raw_summary[:400]}\n\n"
            f"Required JSON:\n"
            f'{{"title_ja":"<Japanese title>","summary_ja":"<2-3 sentence Japanese summary>"}}'
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
        category = "オピニオン" if raw.tier == "opinion" else classify_category(raw.title, raw.raw_summary)
        max_tok = 800 if raw.full_text else 300
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tok,
                messages=[{"role": "user", "content": _build_prompt(raw)}],
            )
            data = json.loads(_extract_json(response.content[0].text))
            articles.append(Article(
                title_en=raw.title,
                title_ja=data.get("title_ja", raw.title),
                summary_en=raw.raw_summary[:300],
                summary_ja=data.get("summary_ja", raw.raw_summary[:300]),
                source=raw.source,
                tier=raw.tier,
                link=raw.link,
                state_media=raw.state_media,
                category=category,
                published=raw.published,
                full_text=raw.full_text,
                translation_ja="",
                vocab=data.get("vocab", []),
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
                full_text=raw.full_text,
                translation_ja="",
                vocab=[],
            ))
        time.sleep(rate_limit_delay)

    return articles
