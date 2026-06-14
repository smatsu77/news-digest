from pathlib import Path
import tempfile
from config import Article
from render import render_html, write_html

def _make_article(**kwargs):
    defaults = dict(
        title_en="Test Headline EN",
        title_ja="テスト見出し JA",
        summary_en="English summary sentence.",
        summary_ja="日本語要約文。",
        source="BBC",
        region="英語圏",
        link="https://bbc.com/news/1",
        state_media=False,
        category="政治",
        published="",
    )
    defaults.update(kwargs)
    return Article(**defaults)

def test_render_html_contains_title():
    html = render_html([_make_article()], "2026-06-14")
    assert "Test Headline EN" in html
    assert "テスト見出し JA" in html

def test_render_html_contains_region():
    html = render_html([_make_article()], "2026-06-14")
    assert "英語圏" in html

def test_render_html_state_media_badge():
    html = render_html([_make_article(state_media=True)], "2026-06-14")
    assert "⚠国営系" in html

def test_render_html_no_badge_for_normal():
    html = render_html([_make_article(state_media=False)], "2026-06-14")
    assert "⚠国営系" not in html

def test_render_html_link_present():
    html = render_html([_make_article()], "2026-06-14")
    assert "https://bbc.com/news/1" in html

def test_render_html_xss_escaped():
    art = _make_article(title_en='<script>alert("xss")</script>')
    html = render_html([art], "2026-06-14")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

def test_write_html_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        docs = Path(tmpdir)
        dated, latest = write_html([_make_article()], docs)
        assert dated.exists()
        assert latest.exists()
        assert "morning-read-" in dated.name
        assert latest.name == "latest.html"
