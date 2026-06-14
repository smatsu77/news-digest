import pytest
from unittest.mock import patch, MagicMock
from config import Source
from fetch import fetch_source, fetch_all

MOCK_ENTRY = {
    "title": "Test Headline",
    "link": "https://example.com/article",
    "summary": "A short summary.",
    "published": "Mon, 14 Jun 2026 03:00:00 GMT",
}

def _make_feed(entries=None, bozo=False):
    feed = MagicMock()
    if entries is None:
        # Create a proper mock entry that returns values from MOCK_ENTRY dict
        mock_entry = MagicMock()
        mock_entry.get = lambda key, default="": MOCK_ENTRY.get(key, default)
        feed.entries = [mock_entry]
    else:
        feed.entries = entries
    feed.bozo = bozo
    feed.bozo_exception = None
    return feed

def test_fetch_source_returns_articles(mocker):
    mocker.patch("feedparser.parse", return_value=_make_feed())
    source = Source("TestSource", "wire", "https://example.com/rss.xml")
    result = fetch_source(source)
    assert len(result) == 1
    assert result[0].title == "Test Headline"
    assert result[0].source == "TestSource"
    assert result[0].tier == "wire"
    assert not result[0].state_media

def test_fetch_source_skips_empty_url():
    source = Source("AFP", "wire", "")
    result = fetch_source(source)
    assert result == []

def test_fetch_source_state_media_flag(mocker):
    mocker.patch("feedparser.parse", return_value=_make_feed())
    source = Source("TASS/RT", "state", "https://tass.com/rss/v2.xml", state_media=True)
    result = fetch_source(source)
    assert result[0].state_media is True

def test_fetch_source_empty_feed_returns_empty(mocker):
    feed = _make_feed(entries=[])
    mocker.patch("feedparser.parse", return_value=feed)
    source = Source("Dead", "wire", "https://dead.example.com/rss")
    result = fetch_source(source)
    assert result == []

def test_fetch_source_exception_returns_empty(mocker):
    mocker.patch("feedparser.parse", side_effect=Exception("timeout"))
    source = Source("Broken", "wire", "https://broken.example.com/rss")
    result = fetch_source(source)  # must not raise
    assert result == []

def test_fetch_source_respects_max_items(mocker):
    entries = []
    for _ in range(20):
        mock_entry = MagicMock()
        mock_entry.get = lambda key, default="", m=MOCK_ENTRY: m.get(key, default)
        entries.append(mock_entry)
    mocker.patch("feedparser.parse", return_value=_make_feed(entries=entries))
    source = Source("Big", "wire", "https://big.example.com/rss")
    result = fetch_source(source)
    assert len(result) <= 10

def test_fetch_all_skips_failed_source(mocker):
    good_feed = _make_feed()
    bad_feed = _make_feed(entries=[])
    sources = [
        Source("Good", "wire", "https://good.com/rss"),
        Source("Bad",  "wire", "https://bad.com/rss"),
    ]
    mocker.patch("feedparser.parse", side_effect=[good_feed, bad_feed])
    result = fetch_all(sources)
    assert len(result) == 1
    assert result[0].source == "Good"
