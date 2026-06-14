from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class Source:
    name: str
    tier: str        # was: region
    url: str
    state_media: bool = False

@dataclass
class RawArticle:
    title: str
    link: str
    source: str
    tier: str        # was: region
    state_media: bool
    raw_summary: str = ""
    published: str = ""

@dataclass
class Article:
    title_en: str
    title_ja: str
    summary_en: str
    summary_ja: str
    source: str
    tier: str        # was: region
    link: str
    state_media: bool
    category: str
    published: str = ""

TIERS = ["wire", "public", "paper", "state"]

TIER_LABELS = {
    "wire":   "通信社",
    "public": "公共放送",
    "paper":  "民間紙",
    "state":  "国営メディア",
}

SOURCES: list[Source] = [
    # 通信社
    Source("Reuters",       "wire",   "https://news.google.com/rss/search?q=site:reuters.com+world&hl=en"),
    Source("AP",            "wire",   "https://news.google.com/rss/search?q=site:apnews.com&hl=en"),
    Source("AFP",           "wire",   ""),  # No public RSS; graceful skip
    # 公共放送
    Source("BBC",           "public", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    Source("Deutsche Welle","public", "https://rss.dw.com/rdf/rss-en-all"),
    # 民間紙
    Source("New York Times","paper",  "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    Source("Wall Street Journal", "paper", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    Source("The Guardian",  "paper",  "https://www.theguardian.com/world/rss"),
    Source("The Economist", "paper",  "https://www.economist.com/international/rss.xml"),
    Source("Le Monde",      "paper",  "https://www.lemonde.fr/en/rss/une.xml"),
    Source("Al Jazeera",    "paper",  "https://www.aljazeera.com/xml/rss/all.xml"),
    Source("Haaretz",       "paper",  "https://news.google.com/rss/search?q=site:haaretz.com&hl=en"),
    Source("The Straits Times", "paper", "https://www.straitstimes.com/rss.xml"),
    Source("The Jakarta Post",  "paper", "https://news.google.com/rss/search?q=site:thejakartapost.com&hl=en"),
    Source("The Hindu",     "paper",  "https://www.thehindu.com/news/international/feeder/default.rss"),
    Source("Focus Taiwan",  "paper",  "https://news.google.com/rss/search?q=site:focustaiwan.tw&hl=en"),
    Source("Folha de S.Paulo", "paper", "https://feeds.folha.uol.com.br/internacional/en/world/rss091.xml"),
    Source("Premium Times", "paper",  "https://www.premiumtimesng.com/feed"),
    # 国営
    Source("Xinhua/CGTN",   "state",  "https://www.cgtn.com/subscribe/rss/section/world.xml", state_media=True),
    Source("TASS/RT",       "state",  "https://tass.com/rss/v2.xml", state_media=True),
]

CATEGORIES = ["政治", "経済", "IT", "社会"]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "政治": ["politi", "government", "election", "president", "prime minister", "parliament",
              "diplomat", "foreign policy", "sanction", "treaty", "summit", "minister",
              "nato", "un ", "congress", "senate", "war", "military", "bilateral"],
    "経済": ["econom", "market", "trade", "gdp", "inflation", "interest rate", "bank",
              "finance", "currency", "stock", "invest", "budget", "fiscal", "monetary",
              "export", "import", "oil price", "energy", "imf", "wto", "tariff"],
    "IT":   ["tech", " ai ", "artificial intelligence", "cyber", "software", "hardware",
              "startup", "digital", "data center", "cloud", "chip", "semiconductor",
              "internet", "social media", "crypto", "blockchain", "robot", "5g", "quantum"],
    "社会": ["social", "health", "education", "climate", "environment", "disaster", "crime",
              "culture", "sport", "science", "covid", "pandemic", "human rights", "protest",
              "migration", "earthquake", "flood", "accident", "refugee"],
}

def classify_category(title: str, raw_summary: str = "") -> str:
    """Keyword-score text; returns best-matching CATEGORY, default '社会'."""
    text = (title + " " + raw_summary).lower()
    scores = {cat: sum(1 for kw in kws if kw in text)
              for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "社会"

def get_env(key: str, required: bool = True) -> Optional[str]:
    val = os.environ.get(key)
    if required and not val:
        raise ValueError(f"Required environment variable {key} is not set")
    return val
