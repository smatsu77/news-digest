from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class Source:
    name: str
    tier: str        # was: region
    url: str
    state_media: bool = False
    fetch_full_text: bool = False  # True for free/open sites where full text is accessible

@dataclass
class RawArticle:
    title: str
    link: str
    source: str
    tier: str        # was: region
    state_media: bool
    raw_summary: str = ""
    full_text: str = ""   # full article body if successfully fetched
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
    full_text: str = ""           # original English full text (if fetched)
    translation_ja: str = ""      # full Japanese translation
    vocab: list = field(default_factory=list)  # difficult words [{word, definition}]

@dataclass
class Coverage:
    region: str
    name: str
    title: str
    link: str
    summary_ja: str
    perspective_ja: str
    state_media: bool = False

@dataclass
class Comparison:
    topic_en: str
    topic_ja: str
    analysis_ja: str
    coverages: list = field(default_factory=list)  # List[Coverage]

TIERS = ["wire", "public", "paper", "opinion", "state"]

TIER_LABELS = {
    "wire":    "通信社",
    "public":  "公共放送",
    "paper":   "民間紙",
    "opinion": "オピニオン",
    "state":   "国営メディア",
}

SOURCES: list[Source] = [
    # 通信社
    Source("Reuters",       "wire",   "https://news.google.com/rss/search?q=site:reuters.com+world&hl=en"),
    Source("AP",            "wire",   "https://feeds.apnews.com/apnews/topnews", fetch_full_text=True),
    Source("AFP",           "wire",   ""),  # No public RSS; graceful skip
    # 公共放送
    Source("BBC World",     "public", "https://feeds.bbci.co.uk/news/world/rss.xml",  fetch_full_text=True),
    Source("BBC UK",        "public", "https://feeds.bbci.co.uk/news/uk/rss.xml",     fetch_full_text=True),
    Source("Deutsche Welle","public", "https://rss.dw.com/rdf/rss-en-all",            fetch_full_text=True),
    Source("ABC News",      "public", "https://feeds.abcnews.com/abcnews/topstories"),
    # 民間紙（無料・全文取得可）
    Source("The Guardian",  "paper",  "https://www.theguardian.com/world/rss",        fetch_full_text=True),
    Source("Al Jazeera",    "paper",  "https://www.aljazeera.com/xml/rss/all.xml",    fetch_full_text=True),
    Source("The Hindu",     "paper",  "https://www.thehindu.com/news/international/feeder/default.rss", fetch_full_text=True),
    Source("Indian Express","paper",  "https://indianexpress.com/feed/"),
    Source("The Star",      "paper",  "https://news.google.com/rss/search?q=site:thestar.com&hl=en"),
    Source("O Globo",       "paper",  "https://news.google.com/rss/search?q=site:oglobo.globo.com/english&hl=en"),
    Source("Premium Times", "paper",  "https://www.premiumtimesng.com/feed",          fetch_full_text=True),
    # 民間紙（有料・RSS抜粋のみ）
    Source("New York Times","paper",  "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    Source("Wall Street Journal", "paper", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
    Source("The Economist", "paper",  "https://www.economist.com/international/rss.xml"),
    Source("Le Monde",      "paper",  "https://www.lemonde.fr/en/rss/une.xml"),
    Source("The Straits Times", "paper", "https://www.straitstimes.com/rss.xml"),
    Source("Haaretz",       "paper",  "https://news.google.com/rss/search?q=site:haaretz.com&hl=en"),
    Source("Focus Taiwan",  "paper",  "https://news.google.com/rss/search?q=site:focustaiwan.tw&hl=en"),
    # 国営
    Source("Xinhua",        "state",  "https://english.news.cn/rss/world.xml", state_media=True),
    Source("CGTN",          "state",  "https://www.cgtn.com/subscribe/rss/section/world.xml", state_media=True),
    Source("TASS/RT",       "state",  "https://tass.com/rss/v2.xml", state_media=True),
    # オピニオン（全文取得）
    Source("Project Syndicate", "opinion", "https://www.project-syndicate.org/rss",   fetch_full_text=True),
    Source("Guardian Opinion",  "opinion", "https://www.theguardian.com/commentisfree/rss", fetch_full_text=True),
    Source("Foreign Affairs",   "opinion", "https://www.foreignaffairs.com/rss.xml",  fetch_full_text=True),
]

CATEGORIES = ["政治", "経済", "IT", "社会", "オピニオン"]

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
