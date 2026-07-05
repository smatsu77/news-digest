from __future__ import annotations
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

from config import SOURCES, get_env
from fetch import fetch_all
from summarize import summarize_articles
from render import write_html
from notify import send_notification
from compare import build_comparison

def _git_push(docs_dir: Path) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d")
    for cmd in [
        ["git", "add", str(docs_dir)],
        ["git", "commit", "-m", f"digest: {date_str} [skip ci]"],
        ["git", "push"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        if r.returncode != 0:
            logger.warning(f"git {cmd[1]} warning: {r.stderr.strip()}")
        else:
            logger.info(f"git {cmd[1]} OK")

def main() -> None:
    public_base = (get_env("PUBLIC_URL_BASE", required=False) or "").rstrip("/")

    logger.info("=== 1/5 Fetching RSS ===")
    raw = fetch_all(SOURCES)
    logger.info(f"Total raw articles: {len(raw)}")
    if not raw:
        logger.error("No articles fetched -- aborting")
        sys.exit(1)

    logger.info("=== 2/5 Summarizing (Anthropic API) ===")
    articles = summarize_articles(raw)
    logger.info(f"Summarized: {len(articles)} articles")

    logger.info("=== 3/6 Building media comparison ===")
    comparison = None
    try:
        comparison = build_comparison(articles)
        if comparison:
            logger.info(f"Comparison built: {comparison.topic_en}")
        else:
            logger.info("Comparison skipped (insufficient coverage)")
    except Exception as exc:
        logger.warning(f"Comparison failed (non-fatal): {exc}")

    logger.info("=== 4/6 Rendering HTML ===")
    docs_dir = Path(__file__).parent / "docs"
    ntfy_topic = get_env("NTFY_TOPIC", required=False) or ""
    dated_path, latest_path = write_html(articles, docs_dir, ntfy_topic=ntfy_topic,
                                         comparison=comparison)
    logger.info(f"HTML: {dated_path.name}, {latest_path.name}")

    logger.info("=== 5/6 Git commit & push ===")
    _git_push(docs_dir)

    logger.info("=== 6/6 ntfy notification ===")
    click_url = f"{public_base}/latest.html" if public_base else ""
    ok = send_notification(articles, click_url)
    if not ok:
        logger.error("ntfy failed -- HTML was committed; continuing")

    logger.info("=== Done ===")

if __name__ == "__main__":
    main()
