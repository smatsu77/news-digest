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

def _build_vocab_prompt(raw: RawArticle) -> str:
    content = raw.full_text[:2500]
    return (
        f"Extract 3-5 advanced vocabulary words (TOEIC 800+ level) from this article.\n"
        f"Output ONLY valid JSON, no markdown fences:\n"
        f'{{"vocab":[{{"word":"<English word>","definition":"<Japanese explanation of meaning and usage, 1-2 sentences>"}}]}}\n\n'
        f"Article:\n{content}"
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

        # 全文なし記事: APIコール不要、RSSデータをそのまま使用
        if not raw.full_text:
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
                full_text="",
                translation_ja="",
                vocab=[],
            ))
            continue

        # 全文あり記事: 単語抽出のみ
        vocab = []
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": _build_vocab_prompt(raw)}],
            )
            data = json.loads(_extract_json(response.content[0].text))
            vocab = data.get("vocab", [])
        except Exception as exc:
            logger.warning(f"Vocab extraction failed for '{raw.title[:60]}': {exc}")

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
            vocab=vocab,
        ))
        time.sleep(rate_limit_delay)

    return articles
