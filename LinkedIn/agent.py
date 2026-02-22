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
        self.fetch_pool_size = news_config.get('fetch_pool_size', 20)
        self.min_value_score = news_config.get('min_value_score', 50)

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
                raise RuntimeError("No config file and could not create from environment variables. Set OPENAI_API_KEY and LINKEDIN_ACCESS_TOKEN.")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

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
                'fetch_method': os.environ.get('NEWS_FETCH_METHOD', 'both'),
                'search_model': os.environ.get('SEARCH_MODEL', 'gpt-4o-mini'),
                'topics': os.environ.get(
                    'NEWS_TOPICS',
                    'OpenAI,NVIDIA,Google AI,Microsoft AI,Meta AI,Anthropic,AI models,generative AI'
                ).split(','),
                'use_multiple_articles': os.environ.get('USE_MULTIPLE_ARTICLES', 'false').lower() == 'true',
                'articles_per_post': int(os.environ.get('ARTICLES_PER_POST', '3')),
                'fetch_pool_size': int(os.environ.get('FETCH_POOL_SIZE', '20')),
                'min_value_score': int(os.environ.get('MIN_VALUE_SCORE', '50'))
            },
            'post': {
                'include_image': os.environ.get('INCLUDE_IMAGE', 'true').lower() == 'true'
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
            articles = self.news_fetcher.get_latest_news(
                limit=self.fetch_pool_size, rank_by_value=rank_by_value
            )

            if not articles:
                logger.warning("No articles found")
                return False

            logger.info(f"Found {len(articles)} articles, selecting best by value score")

            if self.news_scorer:
                self._display_news_analysis(articles)

            articles_needed = self.articles_per_post if self.use_multiple_articles else 1
            top_articles = self._get_top_articles(articles, articles_needed)

            if self.use_multiple_articles and len(top_articles) >= self.articles_per_post:
                selected_articles = top_articles[:self.articles_per_post]
                logger.info(f"Generating multi-article post from {len(selected_articles)} articles")
                post_content = self.post_generator.generate_multi_article_post(selected_articles)
                article = selected_articles[0]
            else:
                article = top_articles[0]
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
            image = None
            include_image = self.config.get('post', {}).get('include_image', True)
            if include_image:
                try:
                    from image_helper import get_image_for_post
                    openai_key = self.config.get('post_generation', {}).get('openai_api_key')
                    image = get_image_for_post(
                        article_url=article.get('url'),
                        article_title=article.get('title', ''),
                        post_content=post_content,
                        openai_api_key=openai_key
                    )
                except Exception as e:
                    logger.warning(f"Could not get image for post: {e}")

            success = self.linkedin_poster.post_to_linkedin(
                post_content=post_content,
                article_url=article.get('url'),
                image=image
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

    def _get_top_articles(self, articles: List[Dict], num_needed: int) -> List[Dict]:
        """
        Filter to high-value articles and return the top N.
        Ensures we only generate posts from the best-scoring content.
        """
        if self.news_scorer and self.min_value_score > 0:
            high_value = [a for a in articles if a.get('value_score', 0) >= self.min_value_score]
            if high_value:
                logger.info(f"Filtered to {len(high_value)} high-value articles (score >= {self.min_value_score})")
                return high_value[:num_needed]
            logger.warning(f"No articles met min score {self.min_value_score}, using top {num_needed} by rank")
        return articles[:num_needed]

    def preview_posts(self, num_posts: int = 3, topics: List[str] = None) -> List[Dict]:
        """
        Preview multiple posts without posting.
        Fetches a large pool, scores all articles, filters to high-value only,
        and generates posts for the TOP articles (best score first).
        """
        logger.info(f"Fetching news pool to find the best {num_posts} articles...")

        if self.use_multiple_articles:
            articles_needed = num_posts * self.articles_per_post
        else:
            articles_needed = num_posts

        # Fetch larger pool, score and rank all
        rank_by_value = self.news_scorer is not None
        articles = self.news_fetcher.get_latest_news(
            limit=self.fetch_pool_size, rank_by_value=rank_by_value, topics=topics
        )

        if not articles:
            return []

        if self.news_scorer:
            self._display_news_analysis(articles)

        # Filter to high-value only, take top N (best first)
        top_articles = self._get_top_articles(articles, articles_needed)

        if not top_articles:
            return []

        previews = []

        if self.use_multiple_articles and len(top_articles) >= self.articles_per_post:
            for i in range(num_posts):
                start_idx = i * self.articles_per_post
                end_idx = start_idx + self.articles_per_post
                if end_idx > len(top_articles):
                    break

                selected_articles = top_articles[start_idx:end_idx]
                score = selected_articles[0].get('value_score', 0)
                logger.info(f"Generating post {i+1}/{num_posts} from top articles (score: {score})")
                post_content = self.post_generator.generate_multi_article_post(selected_articles)
                previews.append({
                    'article': selected_articles[0],
                    'articles': selected_articles,
                    'post': post_content
                })
        else:
            for i, article in enumerate(top_articles[:num_posts]):
                score = article.get('value_score', 0)
                logger.info(f"Generating post {i+1}/{num_posts}: {article.get('title', '')[:50]}... (score: {score})")
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
