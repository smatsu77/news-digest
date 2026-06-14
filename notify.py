from __future__ import annotations
import logging
from typing import List
import requests
from config import Article, REGIONS, get_env

logger = logging.getLogger(__name__)
_MAX_BYTES = 3800
_TOP_PER_REGION = 2

def build_message(articles: List[Article]) -> str:
    lines = ["[Morning Read]\n"]
    for region in REGIONS:
        region_arts = [a for a in articles if a.region == region]
        if not region_arts:
            continue
        lines.append(f"\n[{region}]")
        for art in region_arts[:_TOP_PER_REGION]:
            prefix = "[!]" if art.state_media else "-"
            lines.append(f"{prefix} {art.title_en}")
    msg = "\n".join(lines)
    encoded = msg.encode("utf-8")
    if len(encoded) > _MAX_BYTES:
        msg = encoded[:_MAX_BYTES].decode("utf-8", errors="ignore")
    return msg

def send_notification(articles: List[Article], click_url: str) -> bool:
    topic = get_env("NTFY_TOPIC")
    server = get_env("NTFY_SERVER", required=False) or "https://ntfy.sh"
    token = get_env("NTFY_TOKEN", required=False)

    message = build_message(articles)
    headers: dict[str, str] = {
        "Title": "Morning Read",
        "Tags": "newspaper",
        "Priority": "default",
    }
    if click_url:
        headers["Click"] = click_url
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(
            f"{server}/{topic}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        logger.info(f"ntfy OK: {resp.status_code}")
        return True
    except Exception as exc:
        logger.error(f"ntfy failed: {exc}")
        return False
