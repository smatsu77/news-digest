from pathlib import Path
import tempfile
import json
from config import Article
from render import render_html, write_html, _safe_json

def _make_article(**kwargs):
    defaults = dict(
        title_en="Test Headline EN",
        title_ja="テスト見出し JA",
        summary_en="English summary sentence.",
        summary_ja="日本語要約文。",
        source="BBC",
        tier="public",
        link="https://bbc.com/news/1",
        state_media=False,
        category="政治",
        published="",
    )
    defaults.update(kwargs)
    return Article(**defaults)

def test_render_html_contains_title():
    html = render_html([_make_article()], "2026-06-14")
    assert "テスト見出し JA" in html
    assert "Test Headline EN" in html

def test_render_html_contains_category_tab():
    html = render_html([_make_article()], "2026-06-14")
    assert "政治" in html
    assert "経済" in html
    assert "IT" in html
    assert "社会" in html
    assert "全て" in html
    assert "オピニオン" in html

def test_render_html_state_media_badge():
    html = render_html([_make_article(state_media=True)], "2026-06-14")
    assert "国営系" in html

def test_render_html_no_badge_for_normal():
    html = render_html([_make_article(state_media=False)], "2026-06-14")
    # In the new JS-driven UI the badge text is always in the template but
    # visibility is controlled by JS (state_media flag in JSON).
    # Verify the article's state_media flag is correctly serialised as false.
    assert '"state_media": false' in html

def test_render_html_link_present():
    html = render_html([_make_article()], "2026-06-14")
    assert "https://bbc.com/news/1" in html

def test_render_html_xss_escaped():
    art = _make_article(title_ja='<script>alert("xss")</script>')
    html = render_html([art], "2026-06-14")
    # Should not contain a raw closing script tag that breaks the page
    # The JSON encoder escapes or the replace() handles </script>
    assert "<\\/script>" in html or "<script>alert" not in html

def test_safe_json_escapes_script_tag():
    art = _make_article(title_ja="</script><script>alert(1)</script>")
    result = _safe_json([art])
    assert "</script>" not in result
    assert "<\\/script>" in result

def test_write_html_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        docs = Path(tmpdir)
        dated, latest = write_html([_make_article()], docs)
        assert dated.exists()
        assert latest.exists()
        assert "morning-read-" in dated.name
        assert latest.name == "latest.html"
