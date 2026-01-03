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
        """Fetch news from NewsAPI.org - Focus on OpenAI, NVIDIA, and Tech Giants"""
        if not self.news_api_key or not self.use_news_api:
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            # Focus on OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon AI news
            params = {
                'q': '(OpenAI OR "GPT-4" OR ChatGPT OR Sora OR "NVIDIA" OR "Nvidia" OR "RTX" OR "H100" OR "A100" OR "Google AI" OR Gemini OR "DeepMind" OR "Microsoft AI" OR Copilot OR "Azure AI" OR "Meta AI" OR Llama OR "LLaMA" OR "Apple AI" OR "Amazon AI" OR Bedrock) AND (AI OR "artificial intelligence" OR "machine learning")',
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 30,
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
        """Check if article meets our criteria - Focus on tech giants"""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text = f"{title} {description}"
        
        # Tech giants keywords (at least one must be present)
        tech_giants_keywords = [
            'openai', 'gpt-4', 'gpt-3', 'chatgpt', 'sora', 'dall-e', 'whisper',
            'nvidia', 'nvidia', 'rtx', 'h100', 'a100', 'gh200', 'blackwell', 'cuda',
            'google ai', 'gemini', 'deepmind', 'alphago', 'alphafold', 'palm', 'bert',
            'microsoft ai', 'copilot', 'azure ai', 'bing chat', 'gpt-4 turbo',
            'meta ai', 'llama', 'llama 2', 'llama 3', 'opt', 'galactica',
            'apple ai', 'coreml', 'neural engine', 'siri',
            'amazon ai', 'bedrock', 'alexa', 'sagemaker',
            'anthropic', 'claude', 'claude 3',
            'tesla ai', 'dojo', 'fsd',
            'x ai', 'grok'
        ]
        
        # Check if article mentions any tech giant
        has_tech_giant = any(keyword in text for keyword in tech_giants_keywords)
        
        # Check required keywords (if specified)
        if self.keywords_required:
            has_required = any(keyword.lower() in text for keyword in self.keywords_required)
            if not has_required and not has_tech_giant:
                return False
        
        # If no required keywords specified, at least one tech giant must be mentioned
        if not self.keywords_required and not has_tech_giant:
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

    def get_latest_news(self, limit: int = 5, rank_by_value: bool = False) -> List[Dict]:
        """
        Get latest news from all sources
        
        Args:
            limit: Maximum number of articles to return
            rank_by_value: If True, rank articles by value score (requires news_scorer)
        
        Returns:
            List of article dictionaries, optionally ranked by value
        """
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
        
        # If ranking by value, use NewsScorer
        if rank_by_value:
            try:
                from news_scorer import NewsScorer
                scorer = NewsScorer()
                unique_articles = scorer.rank_articles(unique_articles)
            except ImportError:
                logger.warning("news_scorer not available, sorting by date instead")
                unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        else:
            # Sort by date (newest first)
            unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_articles[:limit]

