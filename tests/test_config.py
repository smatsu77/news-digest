import os
import pytest
from config import (
    Source, RawArticle, Article,
    SOURCES, TIERS, TIER_LABELS, CATEGORIES, CATEGORY_KEYWORDS,
    classify_category, get_env,
)

def test_sources_have_required_fields():
    for s in SOURCES:
        assert s.name
        assert s.tier in TIERS
        # url can be empty string (AFP), but must not be None
        assert s.url is not None

def test_state_media_sources():
    state_media = [s for s in SOURCES if s.state_media]
    names = {s.name for s in state_media}
    assert "Xinhua/CGTN" in names
    assert "TASS/RT" in names
    bbc = next(s for s in SOURCES if s.name == "BBC")
    assert not bbc.state_media

def test_classify_category_politics():
    assert classify_category("President signs new treaty with NATO allies") == "政治"

def test_classify_category_economy():
    assert classify_category("Federal Reserve raises interest rate by 0.25%") == "経済"

def test_classify_category_it():
    assert classify_category("OpenAI releases new AI model") == "IT"

def test_classify_category_society_default():
    assert classify_category("Something happened somewhere") == "社会"

def test_get_env_missing_required(monkeypatch):
    monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
    with pytest.raises(ValueError, match="NONEXISTENT_VAR"):
        get_env("NONEXISTENT_VAR")

def test_get_env_optional_missing(monkeypatch):
    monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
    assert get_env("NONEXISTENT_VAR", required=False) is None

def test_get_env_present(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "hello")
    assert get_env("TEST_KEY") == "hello"
