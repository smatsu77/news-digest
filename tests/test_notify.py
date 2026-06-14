import pytest
from unittest.mock import patch, MagicMock
from config import Article
from notify import build_message, send_notification

def _art(tier="wire", title_en="Headline", state_media=False):
    return Article(
        title_en=title_en, title_ja="見出し",
        summary_en="Summary.", summary_ja="要約。",
        source="Reuters", tier=tier,
        link="https://reuters.com/1",
        state_media=state_media,
        category="政治",
    )

def test_build_message_contains_tier_labels():
    arts = [_art("wire"), _art("public")]
    msg = build_message(arts)
    assert "通信社" in msg
    assert "公共放送" in msg

def test_build_message_contains_headline():
    arts = [_art(title_en="Big News Today")]
    msg = build_message(arts)
    assert "Big News Today" in msg

def test_build_message_state_media_prefix():
    arts = [_art(state_media=True)]
    msg = build_message(arts)
    assert "[!]" in msg

def test_build_message_max_2_per_region():
    arts = [_art(title_en=f"Story {i}") for i in range(5)]
    msg = build_message(arts)
    assert msg.count("Story") <= 2

def test_build_message_under_4kb():
    arts = [_art(title_en="A" * 200) for _ in range(50)]
    msg = build_message(arts)
    assert len(msg.encode("utf-8")) < 4096

def test_send_notification_ok(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "test-topic")
    monkeypatch.delenv("NTFY_TOKEN", raising=False)
    monkeypatch.delenv("NTFY_SERVER", raising=False)
    arts = [_art()]
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        result = send_notification(arts, "https://example.com/latest.html")
    assert result is True
    call_args = mock_post.call_args
    assert "ntfy.sh/test-topic" in call_args[0][0]

def test_send_notification_failure_returns_false(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "test-topic")
    monkeypatch.delenv("NTFY_TOKEN", raising=False)
    monkeypatch.delenv("NTFY_SERVER", raising=False)
    with patch("requests.post", side_effect=Exception("connection error")):
        result = send_notification([_art()], "")
    assert result is False
