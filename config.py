from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class Source:
    name: str
    region: str
    url: str
    state_media: bool = False

@dataclass
class RawArticle:
    title: str
    link: str
    source: str
    region: str
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
    region: str
    link: str
    state_media: bool
    category: str
    published: str = ""

SOURCES: list[Source] = [
    # 英語圏
    Source("BBC",         "英語圏", "https://feeds.bbci.co.uk/news/rss.xml"),
    Source("CNN",         "英語圏", "http://rss.cnn.com/rss/edition.rss"),
    Source("ABC News AU", "英語圏", "https://www.abc.net.au/news/feed/51120/rss.xml"),
    # 韓国
    Source("Yonhap",      "韓国", "https://en.yna.co.kr/RSS/news.xml"),
    Source("Chosun Ilbo", "韓国", "https://www.chosun.com/arc/outboundfeeds/rss/category/english/?outputType=xml"),
    Source("Hankyoreh",   "韓国", "https://english.hani.co.kr/rss/"),
    # 台湾
    Source("Focus Taiwan", "台湾", "https://focustaiwan.tw/rss"),
    Source("Taipei Times", "台湾", "https://www.taipeitimes.com/xml/index.rss"),
    # 中国
    Source("Xinhua",       "中国", "https://english.news.cn/rss/world.xml", state_media=True),
    Source("Global Times", "中国", "https://www.globaltimes.cn/rss/outbrain.xml", state_media=True),
    Source("SCMP",         "中国", "https://www.scmp.com/rss/91/feed"),
    # 中東
    Source("Al Jazeera",     "中東", "https://www.aljazeera.com/xml/rss/all.xml"),
    Source("Al Arabiya",     "中東", "https://english.alarabiya.net/rss.xml"),
    Source("Middle East Eye","中東", "https://www.middleeasteye.net/rss"),
    # ロシア
    Source("TASS",         "ロシア", "https://tass.com/rss/v2.xml", state_media=True),
    Source("Moscow Times", "ロシア", "https://www.themoscowtimes.com/rss/news"),
    Source("RT",           "ロシア", "https://www.rt.com/rss/news/", state_media=True),
    # ブラジル
    Source("Folha de São Paulo", "ブラジル", "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"),
    Source("G1 Globo",           "ブラジル", "https://g1.globo.com/rss/g1/"),
]

REGIONS = ["英語圏", "韓国", "台湾", "中国", "中東", "ロシア", "ブラジル"]
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
