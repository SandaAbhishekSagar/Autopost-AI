"""
Main Agent Orchestrator
Coordinates AI-powered news fetching, post generation, and LinkedIn posting
"""

import yaml
import logging
from typing import Dict, List, Optional
import os
import sys
from news_fetcher import NewsFetcher
from post_generator import PostGenerator
from linkedin_poster import LinkedInPoster

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from news_scorer import NewsScorer
    NEWS_SCORER_AVAILABLE = True
except ImportError:
    NEWS_SCORER_AVAILABLE = False


class LinkedInAIAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the agent with configuration"""
        self.config = self._load_config(config_path)

        # Pass full config so NewsFetcher can access openai key
        self.news_fetcher = NewsFetcher(self.config)
        self.post_generator = PostGenerator(self.config)
        self.linkedin_poster = LinkedInPoster(self.config.get('linkedin', {}))

        news_config = self.config.get('news', {})
        self.use_multiple_articles = news_config.get('use_multiple_articles', False)
        self.articles_per_post = news_config.get('articles_per_post', 3)

        if self.use_multiple_articles:
            logger.info(f"Multi-article storytelling mode ENABLED - will combine {self.articles_per_post} articles per post")
        else:
            logger.info("Single article mode - generating posts from individual articles")

        if NEWS_SCORER_AVAILABLE:
            self.news_scorer = NewsScorer()
            logger.info("News value scoring enabled")
        else:
            self.news_scorer = None

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file or environment variables"""
        if not os.path.exists(config_path):
            logger.warning(f"Config file {config_path} not found. Building from environment variables...")
            config = self._create_config_from_env()
            if config:
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                    logger.info(f"Configuration saved to {config_path}")
                except Exception as e:
                    logger.warning(f"Could not save config: {e}")
                return config
            else:
                logger.error("No config file and could not create from environment variables!")
                sys.exit(1)

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

    def _create_config_from_env(self) -> Optional[Dict]:
        """Create configuration from environment variables"""
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return None

        linkedin_access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
        if not linkedin_access_token:
            logger.warning("LINKEDIN_ACCESS_TOKEN not found in environment variables")
            return None

        config = {
            'profile': {
                'name': os.environ.get('PROFILE_NAME', 'Your Name'),
                'title': os.environ.get('PROFILE_TITLE', 'AI/ML Engineer'),
                'skills': os.environ.get('PROFILE_SKILLS', 'Machine Learning,Deep Learning,Python').split(','),
                'experience_years': int(os.environ.get('PROFILE_EXPERIENCE_YEARS', '5')),
                'expertise_areas': os.environ.get('PROFILE_EXPERTISE', 'AI Research,MLOps').split(',')
            },
            'linkedin': {
                'client_id': os.environ.get('LINKEDIN_CLIENT_ID', ''),
                'client_secret': os.environ.get('LINKEDIN_CLIENT_SECRET', ''),
                'access_token': linkedin_access_token
            },
            'news': {
                'search_model': os.environ.get('SEARCH_MODEL', 'gpt-4o-mini'),
                'topics': os.environ.get(
                    'NEWS_TOPICS',
                    'OpenAI,NVIDIA,Google AI,Microsoft AI,Meta AI,Anthropic,AI models,generative AI'
                ).split(','),
                'use_multiple_articles': os.environ.get('USE_MULTIPLE_ARTICLES', 'false').lower() == 'true',
                'articles_per_post': int(os.environ.get('ARTICLES_PER_POST', '3'))
            },
            'post_generation': {
                'ai_model': os.environ.get('OPENAI_MODEL', 'gpt-4'),
                'openai_api_key': openai_api_key,
                'tone': os.environ.get('POST_TONE', 'professional'),
                'max_post_length': int(os.environ.get('MAX_POST_LENGTH', '3000')),
                'include_hashtags': os.environ.get('INCLUDE_HASHTAGS', 'true').lower() == 'true',
                'hashtags': os.environ.get('HASHTAGS', '#AI,#MachineLearning,#ArtificialIntelligence,#TechNews').split(',')
            },
            'schedule': {
                'enabled': os.environ.get('SCHEDULE_ENABLED', 'true').lower() == 'true',
                'frequency': os.environ.get('SCHEDULE_FREQUENCY', 'daily'),
                'time': os.environ.get('SCHEDULE_TIME', '09:00'),
                'timezone': os.environ.get('SCHEDULE_TIMEZONE', 'UTC')
            }
        }

        return config

    def run(self, dry_run: bool = False) -> bool:
        """
        Main execution: fetch news via AI web search, generate post, publish.

        Args:
            dry_run: If True, generate posts but don't post to LinkedIn
        """
        logger.info("Starting LinkedIn AI Auto-Poster Agent...")

        try:
            logger.info("Searching for latest AI/ML news via OpenAI web search...")
            rank_by_value = self.news_scorer is not None
            limit = max(10, self.articles_per_post * 2) if self.use_multiple_articles else 10
            articles = self.news_fetcher.get_latest_news(limit=limit, rank_by_value=rank_by_value)

            if not articles:
                logger.warning("No articles found")
                return False

            logger.info(f"Found {len(articles)} relevant articles")

            if self.news_scorer:
                self._display_news_analysis(articles)

            if self.use_multiple_articles and len(articles) >= self.articles_per_post:
                selected_articles = articles[:self.articles_per_post]
                logger.info(f"Generating multi-article post from {len(selected_articles)} articles")
                post_content = self.post_generator.generate_multi_article_post(selected_articles)
                article = selected_articles[0]
            else:
                article = articles[0]
                logger.info(f"Generating post for: {article.get('title', 'Unknown')}")
                post_content = self.post_generator.generate_post(article)

            try:
                print("\n" + "=" * 80)
                print("GENERATED POST:")
                print("=" * 80)
                print(post_content)
                print("=" * 80 + "\n")
            except UnicodeEncodeError:
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                print("\n" + "=" * 80)
                print("GENERATED POST:")
                print("=" * 80)
                print(post_content)
                print("=" * 80 + "\n")

            if dry_run:
                logger.info("DRY RUN: Post not sent to LinkedIn")
                return True

            logger.info("Posting to LinkedIn...")
            success = self.linkedin_poster.post_to_linkedin(
                post_content=post_content,
                article_url=article.get('url')
            )

            if success:
                logger.info("Successfully posted to LinkedIn!")
                return True
            else:
                logger.error("Failed to post to LinkedIn")
                return False

        except Exception as e:
            logger.error(f"Error in agent execution: {e}", exc_info=True)
            return False

    def _display_news_analysis(self, articles: List[Dict]) -> None:
        """Display news value analysis and posting frequency recommendations"""
        if not self.news_scorer or not articles:
            return

        try:
            freq_recommendation = self.news_scorer.get_posting_frequency_recommendation(articles)

            print("\n" + "=" * 80)
            print("NEWS VALUE ANALYSIS & POSTING RECOMMENDATIONS")
            print("=" * 80)
            print(f"\nRecommended Frequency: {freq_recommendation['recommended_frequency']}")
            print(f"Reason: {freq_recommendation['reason']}")
            print(f"\nNews Quality:")
            print(f"   High-value (>=60): {freq_recommendation['high_value_count']}")
            print(f"   Medium-value (40-59): {freq_recommendation['medium_value_count']}")
            print(f"   Low-value (<40): {freq_recommendation['low_value_count']}")

            if freq_recommendation.get('top_articles'):
                print(f"\nTop {len(freq_recommendation['top_articles'])} Articles:")
                for i, article in enumerate(freq_recommendation['top_articles'], 1):
                    score = article.get('value_score', 0)
                    title = article.get('title', 'Unknown')[:60]
                    print(f"   {i}. [{score}/110] {title}...")

            print("\n" + "=" * 80 + "\n")
        except Exception as e:
            logger.warning(f"Error displaying news analysis: {e}")

    def preview_posts(self, num_posts: int = 3, topics: List[str] = None) -> List[Dict]:
        """
        Preview multiple posts without posting.

        Args:
            num_posts: Number of posts to preview
            topics: Optional custom topics for news search
        """
        logger.info(f"Generating preview for {num_posts} posts...")

        if self.use_multiple_articles:
            articles_needed = num_posts * self.articles_per_post
        else:
            articles_needed = num_posts

        rank_by_value = self.news_scorer is not None
        articles = self.news_fetcher.get_latest_news(
            limit=articles_needed, rank_by_value=rank_by_value, topics=topics
        )

        if self.news_scorer:
            self._display_news_analysis(articles)

        previews = []

        if self.use_multiple_articles and len(articles) >= self.articles_per_post:
            for i in range(num_posts):
                start_idx = i * self.articles_per_post
                end_idx = start_idx + self.articles_per_post
                if end_idx > len(articles):
                    break

                selected_articles = articles[start_idx:end_idx]
                post_content = self.post_generator.generate_multi_article_post(selected_articles)
                previews.append({
                    'article': selected_articles[0],
                    'articles': selected_articles,
                    'post': post_content
                })
        else:
            for article in articles[:num_posts]:
                post_content = self.post_generator.generate_post(article)
                previews.append({
                    'article': article,
                    'post': post_content
                })

        return previews


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn AI Auto-Poster Agent')
    parser.add_argument('--dry-run', action='store_true', help='Generate posts without posting')
    parser.add_argument('--preview', type=int, metavar='N', help='Preview N posts without posting')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')

    args = parser.parse_args()
    agent = LinkedInAIAgent(config_path=args.config)

    if args.preview:
        previews = agent.preview_posts(num_posts=args.preview)
        for i, preview in enumerate(previews, 1):
            try:
                article = preview['article']
                print(f"\n{'=' * 80}")
                print(f"PREVIEW {i}/{len(previews)}")
                print(f"{'=' * 80}")
                print(f"Article: {article.get('title', 'Unknown')}")
                print(f"Source: {article.get('source', 'Unknown')}")
                print(f"URL: {article.get('url', 'N/A')}")

                if agent.news_scorer and article.get('value_score') is not None:
                    print(f"\nVALUE: {article.get('value_score', 0)}/110 | {article.get('value_priority', 'UNKNOWN')}")

                print(f"\nGenerated Post:\n{preview['post']}")
                print(f"{'=' * 80}\n")
            except UnicodeEncodeError:
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                print(f"\nPREVIEW {i}: {preview['article'].get('title', 'Unknown')}")
                print(preview['post'])
    else:
        success = agent.run(dry_run=args.dry_run)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
