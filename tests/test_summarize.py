import json
import pytest
from unittest.mock import MagicMock, patch
from config import RawArticle, classify_category

def test_classify_politics():
    assert classify_category("President meets with foreign minister at summit") == "政治"

def test_classify_economy():
    assert classify_category("Stock market falls on interest rate hike fears") == "経済"

def test_classify_it():
    assert classify_category("New AI chip from startup breaks records") == "IT"

def test_classify_society_fallback():
    assert classify_category("Dogs are nice") == "社会"

def _make_raw(title="Test Article", state_media=False):
    return RawArticle(
        title=title,
        link="https://example.com/1",
        source="TestSource",
        tier="wire",
        state_media=state_media,
        raw_summary="This is a test article about politics.",
    )

def _mock_response(title_en="EN Title", summary_en="EN summary.", title_ja="JA タイトル", summary_ja="JA 要約。"):
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps({
        "title_en": title_en,
        "summary_en": summary_en,
        "title_ja": title_ja,
        "summary_ja": summary_ja,
    }))]
    return resp

def test_summarize_returns_article(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.messages.create.return_value = _mock_response()
        from summarize import summarize_articles
        result = summarize_articles([_make_raw()])
    assert len(result) == 1
    assert result[0].title_en == "EN Title"
    assert result[0].title_ja == "JA タイトル"
    assert result[0].source == "TestSource"
    assert result[0].tier == "wire"

def test_summarize_falls_back_on_api_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.messages.create.side_effect = Exception("API error")
        from summarize import summarize_articles
        result = summarize_articles([_make_raw("Fallback Title")])
    assert len(result) == 1
    assert result[0].title_en == "Fallback Title"

def test_summarize_sets_state_media_flag(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.messages.create.return_value = _mock_response()
        from summarize import summarize_articles
        result = summarize_articles([_make_raw(state_media=True)])
    assert result[0].state_media is True

def test_summarize_skips_empty_title(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("anthropic.Anthropic") as mock_cls:
        from summarize import summarize_articles
        result = summarize_articles([_make_raw(title="")])
    assert len(result) == 0
