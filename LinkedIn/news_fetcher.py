"""
News Fetcher Module
Fetches latest AI/ML news from various sources
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from bs4 import BeautifulSoup
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self, config: Dict):
        self.config = config
        self.news_api_key = config.get('news_api_key')
        self.use_news_api = config.get('use_news_api', False)
        self.rss_feeds = config.get('rss_feeds', [])
        self.sources = config.get('sources', [])
        self.keywords_required = config.get('keywords_required', [])
        self.keywords_excluded = config.get('keywords_excluded', [])
        self.min_age_hours = config.get('min_article_age_hours', 0)
        self.max_age_hours = config.get('max_article_age_hours', 48)

    def fetch_from_news_api(self) -> List[Dict]:
        """Fetch news from NewsAPI.org"""
        if not self.news_api_key or not self.use_news_api:
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'AI OR "machine learning" OR "artificial intelligence"',
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 20,
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                if self._is_valid_article(article):
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'Unknown')
                    })
            
            return articles
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []

    def fetch_from_rss(self) -> List[Dict]:
        """Fetch news from RSS feeds"""
        articles = []
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Limit to 10 per feed
                    article = {
                        'title': entry.get('title', ''),
                        'description': self._extract_description(entry),
                        'url': entry.get('link', ''),
                        'published_at': self._parse_date(entry.get('published', '')),
                        'source': feed.feed.get('title', 'Unknown')
                    }
                    
                    if self._is_valid_article(article):
                        articles.append(article)
                
                time.sleep(1)  # Be respectful to servers
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_url}: {e}")
        
        return articles

    def _extract_description(self, entry) -> str:
        """Extract description from RSS entry"""
        if 'summary' in entry:
            return entry.summary
        elif 'description' in entry:
            return entry.description
        else:
            return ''

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO format"""
        try:
            if hasattr(date_str, 'timetuple'):
                return date_str.isoformat()
            # Try parsing common date formats
            for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except:
                    continue
            return date_str
        except:
            return date_str

    def _is_valid_article(self, article: Dict) -> bool:
        """Check if article meets our criteria"""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text = f"{title} {description}"
        
        # Check required keywords
        if self.keywords_required:
            if not any(keyword.lower() in text for keyword in self.keywords_required):
                return False
        
        # Check excluded keywords
        if self.keywords_excluded:
            if any(keyword.lower() in text for keyword in self.keywords_excluded):
                return False
        
        # Check age
        published_at = article.get('published_at', '')
        if published_at:
            try:
                if 'T' in published_at:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                else:
                    pub_date = datetime.strptime(published_at, '%Y-%m-%d %H:%M:%S')
                
                age_hours = (datetime.now(pub_date.tzinfo) - pub_date).total_seconds() / 3600
                
                if age_hours < self.min_age_hours or age_hours > self.max_age_hours:
                    return False
            except Exception as e:
                logger.warning(f"Could not parse date {published_at}: {e}")
        
        return True

    def get_latest_news(self, limit: int = 5) -> List[Dict]:
        """Get latest news from all sources"""
        all_articles = []
        
        if self.use_news_api:
            all_articles.extend(self.fetch_from_news_api())
        
        all_articles.extend(self.fetch_from_rss())
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_articles[:limit]

