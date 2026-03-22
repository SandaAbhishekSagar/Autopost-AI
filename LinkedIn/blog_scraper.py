"""
Personal Blog Scraper Module
Fetches blog posts from abhisheksagarsanda.com via the site's Netlify serverless
API endpoint (/.netlify/functions/blog-list), which returns full post metadata
as JSON — no JavaScript rendering required.

Falls back to RSS feed parsing when the API is unavailable.
"""

import logging
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from html import unescape

logger = logging.getLogger(__name__)

DEFAULT_BLOG_URL = "https://www.abhisheksagarsanda.com/blog"
DEFAULT_BLOG_API = "https://www.abhisheksagarsanda.com/.netlify/functions/blog-list"
DEFAULT_BLOG_SOURCE = "Abhishek Sagar Sanda's Blog"
DEFAULT_BLOG_BASE = "https://www.abhisheksagarsanda.com"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.abhisheksagarsanda.com/blog",
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> str:
    """Parse various date formats to ISO 8601 UTC string."""
    if not date_str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = date_str.strip()
    formats = [
        "%B %d, %Y",              # March 22, 2026
        "%b %d, %Y",              # Mar 22, 2026
        "%Y-%m-%d",
        "%d %B %Y",
        "%a, %d %b %Y %H:%M:%S %Z",  # RFC 822 (RSS)
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return unescape(text).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 1: Netlify serverless API  (all posts, full metadata)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_via_api(api_url: str, base_url: str, source: str) -> List[Dict]:
    """
    Call the /.netlify/functions/blog-list endpoint and return normalised post dicts.

    The endpoint returns:
        {"posts": [{slug, title, excerpt, date, readTime, tags, ...}, ...]}
    """
    try:
        resp = requests.get(api_url, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug(f"Blog API fetch failed ({api_url}): {e}")
        return []

    raw_posts = data if isinstance(data, list) else data.get("posts", [])
    if not raw_posts:
        logger.debug("Blog API returned empty posts array")
        return []

    domain = re.match(r"(https?://[^/]+)", base_url)
    domain_str = domain.group(1) if domain else DEFAULT_BLOG_BASE

    posts = []
    for item in raw_posts:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug", "")
        title = item.get("title", "")
        if not slug or not title:
            continue

        excerpt = _strip_html(item.get("excerpt", "") or item.get("description", "") or title)
        date_str = item.get("date", "") or item.get("publishedAt", "") or item.get("published_at", "")
        raw_tags = item.get("tags", []) or item.get("categories", [])
        tags = [t.strip() for t in raw_tags if isinstance(t, str) and t.strip()]

        # Some API responses embed comma-separated tag strings
        if not tags and isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

        image_url = item.get("image", "") or item.get("featuredImage", "") or item.get("coverImage", "")
        if image_url and image_url.startswith("/"):
            image_url = domain_str + image_url

        url = item.get("url", "") or item.get("link", "") or f"{domain_str}/blog/{slug}"
        if url.startswith("/"):
            url = domain_str + url

        posts.append({
            "title": title,
            "description": excerpt,
            "url": url,
            "source": source,
            "published_at": _parse_date(date_str),
            "image_url": image_url or None,
            "tags": tags,
            "content_type": "blog",
        })

    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 2: RSS feed  (limited — only a few pinned posts)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_via_rss(rss_url: str, source: str) -> List[Dict]:
    """Parse the blog's RSS feed using feedparser."""
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed. Run: pip install feedparser")
        return []

    try:
        resp = requests.get(rss_url, headers=REQUEST_HEADERS, timeout=12)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        logger.debug(f"RSS fetch failed ({rss_url}): {e}")
        return []

    posts = []
    for entry in feed.entries:
        link = getattr(entry, "link", "") or ""
        title = getattr(entry, "title", "") or ""
        if not title or not link:
            continue

        description = _strip_html(
            getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        )

        # Tags from category string (blog uses comma-separated category element)
        tags: List[str] = []
        cat_str = getattr(entry, "category", "")
        if cat_str:
            tags = [t.strip() for t in cat_str.split(",") if t.strip()]

        # Published date
        pub_date = ""
        for attr in ("published", "updated", "created"):
            val = getattr(entry, attr, "")
            if val:
                pub_date = val
                break

        posts.append({
            "title": title,
            "description": description or title,
            "url": link,
            "source": source,
            "published_at": _parse_date(pub_date),
            "image_url": None,
            "tags": tags,
            "content_type": "blog",
        })

    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def scrape_blog(
    blog_url: str = DEFAULT_BLOG_URL,
    limit: int = 10,
    source: str = DEFAULT_BLOG_SOURCE,
    max_age_hours: Optional[int] = None,
    enrich_posts: bool = False,
) -> List[Dict]:
    """
    Fetch blog posts from abhisheksagarsanda.com.

    Priority:
    1. Netlify API  — /.netlify/functions/blog-list  (30+ posts, full metadata)
    2. RSS feed     — /rss.xml                        (4 featured posts, fallback)

    Args:
        blog_url:       Blog base URL (used to derive domain and API endpoint)
        limit:          Maximum number of posts to return
        source:         Source label attached to each post dict
        max_age_hours:  Only return posts published within N hours (None = no filter)
        enrich_posts:   Unused (kept for API compatibility)

    Returns:
        List of post dicts: title, description, url, source, published_at,
        image_url, tags, content_type
    """
    domain_match = re.match(r"(https?://[^/]+)", blog_url)
    domain_str = domain_match.group(1) if domain_match else DEFAULT_BLOG_BASE

    # Derive the API URL from the blog domain
    api_url = domain_str + "/.netlify/functions/blog-list"
    logger.info(f"Fetching blog posts via API: {api_url}")

    posts = _fetch_via_api(api_url, blog_url, source)

    if not posts:
        logger.info("API returned no posts, falling back to RSS feed...")
        rss_url = domain_str + "/rss.xml"
        posts = _fetch_via_rss(rss_url, source)

    if not posts:
        logger.warning("No blog posts found via any strategy")
        return []

    logger.info(f"Found {len(posts)} posts before filtering")

    # Deduplicate by URL
    seen_urls: set = set()
    unique: List[Dict] = []
    for p in posts:
        url = p.get("url", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(p)
    posts = unique

    # Sort newest-first
    def _sort_key(p: Dict):
        try:
            return datetime.fromisoformat(p.get("published_at", "").replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    posts.sort(key=_sort_key, reverse=True)

    # Optional age filter (blog posts don't expire like news, but useful for "new posts only")
    if max_age_hours and max_age_hours > 0:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        filtered = []
        for p in posts:
            pub_str = p.get("published_at", "").replace("Z", "").strip()
            try:
                pub = datetime.fromisoformat(pub_str)
                if pub >= cutoff:
                    filtered.append(p)
            except Exception:
                filtered.append(p)
        posts = filtered

    result = posts[:limit]
    logger.info(f"Returning {len(result)} blog posts")
    return result
