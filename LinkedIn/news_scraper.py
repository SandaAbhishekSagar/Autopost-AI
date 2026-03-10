"""
RSS News Scraper Module
Scrapes tech news RSS feeds for latest AI/ML articles with images.
Provides reliable images via enclosure/media tags without visiting each article.
"""

import logging
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional
from html import unescape

logger = logging.getLogger(__name__)

# AI/ML keywords to filter articles for relevance
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "openai", "chatgpt",
    "gpt-4", "gpt-5", "claude", "anthropic", "gemini", "google ai",
    "nvidia", "h100", "blackwell", "gpu", "llm", "large language model",
    "meta ai", "llama", "microsoft", "copilot", "deepmind",
    "generative", "transformer", "neural", "startup", "funding",
    "acquisition", "partnership", "launch", "release", "announcement"
]

# RSS feeds from top tech publications (AI/tech coverage)
RSS_FEEDS = [
    {"url": "https://techcrunch.com/feed/", "source": "TechCrunch"},
    {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge"},
    {"url": "https://venturebeat.com/feed/", "source": "VentureBeat"},
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "source": "Ars Technica"},
    {"url": "https://www.wired.com/feed/rss", "source": "Wired"},
    {"url": "https://www.engadget.com/rss.xml", "source": "Engadget"},
    {"url": "https://www.zdnet.com/news/rss.xml", "source": "ZDNet"},
    {"url": "https://www.reuters.com/technology/rss", "source": "Reuters"},
    {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "source": "CNBC"},
]

# Headers to avoid blocks
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def strip_html(html: str) -> str:
    """Remove HTML tags and decode entities"""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    return unescape(text).strip()


def _get_url(obj, *keys) -> Optional[str]:
    """Get URL from dict or object"""
    for k in keys:
        val = obj.get(k) if isinstance(obj, dict) else getattr(obj, k, None)
        if val and isinstance(val, str) and val.startswith("http"):
            return val
    return None


def extract_image_from_entry(entry) -> Optional[str]:
    """Extract image URL from RSS entry (enclosure, media:content, media:thumbnail)"""
    # enclosure (standard RSS)
    enclosures = getattr(entry, "enclosures", []) or []
    for enc in enclosures:
        enc_type = (getattr(enc, "type", None) or enc.get("type") if isinstance(enc, dict) else "") or ""
        enc_url = _get_url(enc, "href", "url")
        if enc_url:
            if "image" in enc_type.lower() or not enc_type or enc_type.startswith("image"):
                return enc_url
            # Some feeds use generic enclosure for images
            if any(ext in enc_url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                return enc_url

    # media:content (Media RSS)
    media_content = getattr(entry, "media_content", []) or []
    if media_content:
        mc = media_content[0]
        url = _get_url(mc, "url", "href")
        if url:
            return url

    # media:thumbnail
    media_thumbnail = getattr(entry, "media_thumbnail", []) or []
    if media_thumbnail:
        mt = media_thumbnail[0]
        url = _get_url(mt, "url", "href")
        if url:
            return url

    # Image in summary/content
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    if summary:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(summary), re.I)
        if img_match:
            return img_match.group(1)

    return None


def parse_published(entry) -> str:
    """Parse published date to ISO format (UTC).
    feedparser returns UTC struct_time; use timegm (not mktime) to avoid timezone shift.
    """
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                from calendar import timegm
                # parsed is UTC struct_time; mktime() would treat it as local time (wrong)
                ts = timegm(parsed)
                dt = datetime.utcfromtimestamp(ts)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except (TypeError, ValueError, OSError):
                pass
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def is_ai_related(text: str) -> bool:
    """Check if text mentions AI/ML topics"""
    lower = text.lower()
    return any(kw in lower for kw in AI_KEYWORDS)


def fetch_feed(feed_url: str, source: str, timeout: int = 10) -> List[Dict]:
    """Fetch and parse a single RSS feed"""
    articles = []
    try:
        resp = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        logger.debug(f"Failed to fetch {feed_url}: {e}")
        return []

    try:
        import feedparser
        feed = feedparser.parse(resp.content)
    except ImportError:
        logger.warning("feedparser not installed. Run: pip install feedparser")
        return []
    except Exception as e:
        logger.debug(f"Failed to parse feed {feed_url}: {e}")
        return []

    for entry in feed.entries[:25]:  # Limit per feed
        link = getattr(entry, "link", "") or ""
        title = strip_html(getattr(entry, "title", "") or "")
        if not title or not link:
            continue

        description = strip_html(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
        text = f"{title} {description}"

        if not is_ai_related(text):
            continue

        image_url = extract_image_from_entry(entry)
        published = parse_published(entry)

        articles.append({
            "title": title,
            "description": description[:500] if description else title,
            "url": link,
            "source": source,
            "published_at": published,
            "image_url": image_url,
        })

    return articles


def scrape_news(limit: int = 20, feeds: Optional[List[Dict]] = None,
                max_age_hours: Optional[int] = 72) -> List[Dict]:
    """
    Scrape news from RSS feeds, filter for AI relevance, dedupe by URL.
    Only keeps articles from the last max_age_hours (default 72 = 3 days) so results are latest.

    Args:
        limit: Max articles to return
        feeds: Optional list of {"url": "...", "source": "..."} to override defaults
        max_age_hours: Drop articles older than this many hours (None = no filter)

    Returns:
        List of article dicts with title, description, url, source, published_at, image_url
    """
    feed_list = feeds or RSS_FEEDS
    all_articles = []
    seen_urls = set()
    cutoff_utc = None
    if max_age_hours is not None and max_age_hours > 0:
        from datetime import timedelta
        cutoff_utc = datetime.utcnow() - timedelta(hours=max_age_hours)

    for feed in feed_list:
        url = feed.get("url", "")
        source = feed.get("source", "Unknown")
        if not url:
            continue
        articles = fetch_feed(url, source)
        for a in articles:
            u = a.get("url", "")
            if u and u not in seen_urls:
                if cutoff_utc is not None:
                    try:
                        pub_str = a.get("published_at", "").replace("Z", "").strip()
                        pub = datetime.fromisoformat(pub_str)
                        if getattr(pub, "tzinfo", None):
                            pub = (pub - pub.utcoffset()).replace(tzinfo=None)
                        if pub < cutoff_utc:
                            continue
                    except Exception:
                        pass
                seen_urls.add(u)
                all_articles.append(a)

    # Sort by published_at (newest first)
    def sort_key(a):
        try:
            return datetime.fromisoformat(a.get("published_at", "").replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    all_articles.sort(key=sort_key, reverse=True)
    logger.info(f"Scraped {len(all_articles)} AI-related articles from RSS feeds (max_age_hours={max_age_hours})")
    return all_articles[:limit]
