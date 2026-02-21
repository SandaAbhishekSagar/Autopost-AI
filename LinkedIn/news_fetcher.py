"""
AI-Powered News Fetcher Module
Uses OpenAI's web_search tool (Responses API) to fetch latest AI/ML news
instead of traditional RSS/API scraping.

Docs: https://platform.openai.com/docs/guides/tools-web-search
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Reputable tech news domains for domain-filtered search
TRUSTED_DOMAINS = [
    "theverge.com",
    "techcrunch.com",
    "reuters.com",
    "bloomberg.com",
    "wired.com",
    "venturebeat.com",
    "arstechnica.com",
    "theinformation.com",
    "cnbc.com",
    "bbc.com",
    "nytimes.com",
    "wsj.com",
    "thenextweb.com",
    "engadget.com",
    "zdnet.com",
    "tomsguide.com",
]


class NewsFetcher:
    """Fetches latest AI/ML news using OpenAI's web_search tool"""

    DEFAULT_TOPICS = [
        "OpenAI", "NVIDIA", "Google AI", "Microsoft AI",
        "Meta AI", "Anthropic", "AI models", "machine learning",
        "deep learning", "LLM", "generative AI"
    ]

    def __init__(self, config: Dict):
        self.config = config
        openai_key = config.get('post_generation', {}).get('openai_api_key', '')
        if not openai_key:
            raise ValueError("OpenAI API key is required for AI-powered news fetching")

        self.client = OpenAI(api_key=openai_key)
        news_config = config.get('news', {})
        self.search_model = news_config.get('search_model', 'gpt-4o-mini')
        self.topics = news_config.get('topics', self.DEFAULT_TOPICS)
        self.fetch_pool_size = news_config.get('fetch_pool_size', 20)

    def get_latest_news(self, limit: int = 10, rank_by_value: bool = False,
                        topics: Optional[List[str]] = None) -> List[Dict]:
        """
        Get latest AI/ML news using OpenAI web search.

        Args:
            limit: Maximum number of articles to return
            rank_by_value: If True, rank articles by value score
            topics: Optional custom topics to search for

        Returns:
            List of article dictionaries
        """
        search_topics = topics or self.topics
        articles = self._search_news(search_topics, limit)

        if not articles:
            logger.warning("No articles found from web search")
            return []

        logger.info(f"Found {len(articles)} articles via AI web search")

        if rank_by_value:
            try:
                from news_scorer import NewsScorer
                scorer = NewsScorer()
                articles = scorer.rank_articles(articles)
            except ImportError:
                logger.warning("news_scorer not available, returning articles as-is")

        return articles[:limit]

    def _search_news(self, topics: List[str], limit: int) -> List[Dict]:
        """Search for news using OpenAI's web_search tool"""
        topics_str = ", ".join(topics[:10])
        fetch_count = max(limit, self.fetch_pool_size)

        prompt = f"""Search the web for the HIGHEST-VALUE AI technology news from the past 48 hours.

Focus on these topics and companies: {topics_str}

PRIORITIZE articles that are HIGH-IMPACT:
- Major announcements (OpenAI, NVIDIA, Google, Microsoft, Meta, Anthropic, Apple, Amazon)
- Product launches and new model releases (GPT-4, Claude, Gemini, Llama, ChatGPT updates)
- Significant funding rounds, acquisitions, or partnerships
- Breakthroughs in AI research, chips (H100, Blackwell), or infrastructure
- Strategic moves by tech giants in AI

Exclude: routine blog posts, opinion pieces, minor updates.

Return ONLY a valid JSON array with up to {fetch_count} articles. No markdown, no code blocks - just the raw JSON:

[
  {{
    "title": "Exact article headline",
    "description": "2-3 sentence summary with key facts, numbers, and company names",
    "url": "Full URL to the article",
    "source": "Publication name (e.g., The Verge, TechCrunch, Reuters)",
    "published_at": "ISO 8601 date (e.g., 2026-02-18T10:30:00Z)"
  }}
]

Requirements:
- Only real articles with working URLs from reputable tech publications
- Sort by impact and recency (highest-value first)
- Include specific product names, funding amounts, company names in descriptions
- Return ONLY the JSON array"""

        result = self._call_web_search(prompt)
        if not result:
            return []

        raw_text, citation_urls = result
        articles = self._parse_articles(raw_text)

        # Enrich articles with citation URLs if the model returned them
        if citation_urls:
            self._enrich_with_citations(articles, citation_urls)

        return articles

    def _call_web_search(self, prompt: str) -> Optional[tuple]:
        """
        Call OpenAI with web search, returning (text, citation_urls).
        Uses a 3-tier fallback strategy.
        """

        # Strategy 1: Responses API with web_search tool (GA)
        try:
            logger.info(f"Fetching news via Responses API web_search with {self.search_model}...")
            response = self.client.responses.create(
                model=self.search_model,
                tools=[{"type": "web_search"}],
                input=prompt
            )
            text = response.output_text
            citations = self._extract_citations(response)
            if text and len(text) > 50:
                logger.info("Successfully fetched news via Responses API (web_search)")
                return text, citations
        except Exception as e:
            logger.info(f"Responses API web_search failed: {e}")

        # Strategy 1b: Try web_search_preview if web_search GA isn't available
        try:
            logger.info("Trying Responses API with web_search_preview...")
            response = self.client.responses.create(
                model=self.search_model,
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            text = response.output_text
            citations = self._extract_citations(response)
            if text and len(text) > 50:
                logger.info("Successfully fetched news via Responses API (web_search_preview)")
                return text, citations
        except Exception as e:
            logger.info(f"Responses API web_search_preview failed: {e}")

        # Strategy 2: Chat Completions with dedicated search models
        for model in ["gpt-5-search-api", "gpt-4o-search-preview", "gpt-4o-mini-search-preview"]:
            try:
                logger.info(f"Trying Chat Completions with {model}...")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.choices[0].message.content
                if text and len(text) > 50:
                    logger.info(f"Successfully fetched news via {model}")
                    return text, []
            except Exception as e:
                logger.info(f"{model} not available: {e}")

        # Strategy 3: Standard model fallback (no live web search)
        try:
            logger.info("Falling back to standard model (no live web search)...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI technology news reporter. Based on your knowledge, provide the most recent and important AI news developments. Return realistic and accurate information."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            text = response.choices[0].message.content
            if text:
                logger.info("Retrieved news from standard model knowledge")
                return text, []
        except Exception as e:
            logger.error(f"All news fetching strategies failed: {e}")

        return None

    def _extract_citations(self, response) -> List[Dict]:
        """Extract url_citation annotations from a Responses API response"""
        citations = []
        try:
            for item in response.output:
                if getattr(item, 'type', None) == 'message':
                    for content_block in getattr(item, 'content', []):
                        for annotation in getattr(content_block, 'annotations', []):
                            if getattr(annotation, 'type', None) == 'url_citation':
                                citations.append({
                                    'url': getattr(annotation, 'url', ''),
                                    'title': getattr(annotation, 'title', '')
                                })
        except Exception as e:
            logger.debug(f"Could not extract citations: {e}")
        return citations

    def _enrich_with_citations(self, articles: List[Dict], citations: List[Dict]) -> None:
        """Fill in missing article URLs from citation annotations"""
        citation_map = {c['title'].lower().strip(): c['url'] for c in citations if c.get('title') and c.get('url')}

        for article in articles:
            if article.get('url'):
                continue
            title_lower = article.get('title', '').lower().strip()
            for cit_title, cit_url in citation_map.items():
                if title_lower in cit_title or cit_title in title_lower:
                    article['url'] = cit_url
                    break

    def _parse_articles(self, raw_text: str) -> List[Dict]:
        """Parse the response text to extract structured article data"""
        text = raw_text.strip()

        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            start = 1
            end = len(lines)
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip().startswith("```"):
                    end = i
                    break
            text = "\n".join(lines[start:end]).strip()

        articles = self._try_parse_json(text)
        if articles:
            return articles

        # Try extracting JSON array from surrounding text
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            articles = self._try_parse_json(json_match.group())
            if articles:
                return articles

        logger.error("Could not parse articles from AI response")
        return []

    def _try_parse_json(self, text: str) -> Optional[List[Dict]]:
        """Attempt to parse JSON text into a list of article dicts"""
        try:
            data = json.loads(text)
            if not isinstance(data, list):
                return None

            valid_articles = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                if not item.get('title'):
                    continue

                article = {
                    'title': str(item.get('title', '')).strip(),
                    'description': str(item.get('description', '')).strip(),
                    'url': str(item.get('url', '')).strip(),
                    'source': str(item.get('source', 'Unknown')).strip(),
                    'published_at': str(item.get('published_at', datetime.now().isoformat())).strip()
                }
                valid_articles.append(article)

            return valid_articles if valid_articles else None
        except (json.JSONDecodeError, ValueError):
            return None
